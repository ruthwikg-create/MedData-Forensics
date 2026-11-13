"""Reproducible and deliberately modest CPU-only evaluation laboratories."""
from __future__ import annotations
from collections import Counter,defaultdict
import hashlib, json, os, platform, random, sys, time, subprocess
from pathlib import Path
from types import SimpleNamespace
import joblib, numpy as np, sklearn, scipy
from PIL import Image, ImageEnhance,ImageFilter
from sqlalchemy import select
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,balanced_accuracy_score,f1_score,roc_auc_score,confusion_matrix,classification_report
from .db import Session,Dataset,Sample,Finding,Review,Experiment,AuditRun,ARTIFACT_ROOT,DATA_ROOT,now,jd,jl
from .analysis_engine import extract_features,DETECTOR_VERSION
from .security import safe_path,sha_file,manifest_hash

LAB_VERSION='labs-0.9.2'

def _load(db,dataset_id):
    d=db.get(Dataset,dataset_id)
    if not d:raise ValueError('Unknown dataset')
    rows=db.scalars(select(Sample).where(Sample.dataset_id==dataset_id).order_by(Sample.sample_id)).all()
    return d,[s for s in rows if s.width and s.height]

def _select_training_subset(train,max_train=2400,seed=42):
    """Preserve each observed class when bounding CPU training cost.

    The returned subset is deterministic for a fixed archive/sample order and
    seed. Capping the training set changes prevalence and must be recorded.
    """
    train=list(train)
    if len(train)<=max_train:return train
    from .ingest import _stratified_subset_indices
    indices=_stratified_subset_indices([s.label for s in train],max_train,seed=seed)
    return [train[int(i)] for i in indices]


def _model(train,seed=42,max_train=2400):
    train=_select_training_subset(train,max_train,seed)
    if len(train)<20 or len(set(x.label for x in train))<2:raise ValueError('Requires >=20 training images and >=2 classes')
    counts=Counter(x.label for x in train)
    # A rare class with one or two samples is allowed for a diagnostic software smoke test.
    # Such a model is NOT validated or reliable; prominently report low support below.
    x=np.vstack([extract_features(safe_path(s.relpath)) for s in train]);y=np.array([s.label for s in train]);
    model=LogisticRegression(max_iter=500,class_weight='balanced',solver='lbfgs',random_state=seed)
    model.fit(x,y)
    return model

def _pred(model,samples):
    x=np.vstack([extract_features(safe_path(s.relpath)) for s in samples]);probs=model.predict_proba(x)
    return probs


def _evaluation_integrity(train, validation, test):
    """Exclude entire cross-split identity components, including transitive links.

    A sample can bridge otherwise different groups or image hashes. Checking
    each record against only the immediately preceding split misses such
    links and can produce misleading held-out performance. Within a split,
    pixel-identical images are also counted just once in evaluation metrics.
    Different images from one patient are retained for cluster bootstrap.
    """
    from .analysis_engine import pixel_fingerprint
    ordered = list(train) + list(validation) + list(test)
    parent = list(range(len(ordered)))
    sizes = [1] * len(ordered)
    tokens = []
    pixel_identities = []
    owners = {}

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def join(a, b):
        a, b = root(a), root(b)
        if a == b:
            return
        if sizes[a] < sizes[b]:
            a, b = b, a
        parent[b] = a
        sizes[a] += sizes[b]

    for index, sample in enumerate(ordered):
        values = set()
        if sample.group_id:
            values.add(('group', sample.group_type or 'unspecified', sample.group_id))
        if sample.sha256:
            values.add(('file_sha256', sample.sha256))
        px = sample.pixelhash or pixel_fingerprint(safe_path(sample.relpath))
        pixel_identities.append(px)
        values.add(('pixel_sha256', px))
        tokens.append(values)
        for token in values:
            if token in owners:
                join(index, owners[token])
            else:
                owners[token] = index

    n_train, n_val = len(train), len(validation)
    train_components = {root(i) for i in range(n_train)}
    val_components = {root(i) for i in range(n_train, n_train + n_val)}
    forbidden_test = train_components | val_components
    keep_validation, keep_test = [], []
    excluded_validation, excluded_test = [], []
    duplicates_validation, duplicates_test = [], []
    seen_val_pixels, seen_test_pixels = set(), set()
    for index in range(n_train, n_train + n_val):
        sample = ordered[index]
        if root(index) in train_components:
            excluded_validation.append(sample.sample_id)
        elif pixel_identities[index] in seen_val_pixels:
            duplicates_validation.append(sample.sample_id)
        else:
            keep_validation.append(sample)
            seen_val_pixels.add(pixel_identities[index])
    for index in range(n_train + n_val, len(ordered)):
        sample = ordered[index]
        if root(index) in forbidden_test:
            excluded_test.append(sample.sample_id)
        elif pixel_identities[index] in seen_test_pixels:
            duplicates_test.append(sample.sample_id)
        else:
            keep_test.append(sample)
            seen_test_pixels.add(pixel_identities[index])
    if not keep_test:
        raise ValueError('No leakage-screened independent test records remain; correct dataset partitions before evaluating')
    meta = {
        'method': 'transitive cross-split identity components from file hashes, decoded pixels and declared group identifiers; one vote per unique image within each evaluation split',
        'train_n': n_train, 'validation_original_n': n_val, 'validation_retained_n': len(keep_validation),
        'test_original_n': len(test), 'test_retained_n': len(keep_test),
        'excluded_validation_sample_ids': (excluded_validation + duplicates_validation)[:100],
        'excluded_test_sample_ids': (excluded_test + duplicates_test)[:100],
        'excluded_validation_n': len(excluded_validation) + len(duplicates_validation),
        'excluded_test_n': len(excluded_test) + len(duplicates_test),
        'duplicate_validation_n': len(duplicates_validation), 'duplicate_test_n': len(duplicates_test),
        'group_ids_missing_n': sum(not x.group_id for x in ordered),
        'limitations': [
            'Available metadata cannot establish patient independence when patient identifiers are absent.',
            'Near duplicates and acquisition-level correlations may remain; run the forensic audit and document test-set provenance.',
            'Leakage filtering was based solely on identity and recorded metadata, never test labels or performance.',
            'Repeated identical evaluation images are not treated as independent observations.'
        ]
    }
    return keep_validation, keep_test, meta


def _cluster_bootstrap_metrics(y, pred, sample_rows, labels, seed=42, repetitions=300):
    """Cluster-resample test observations by declared group when available."""
    rng=np.random.default_rng(seed)
    groups=defaultdict(list)
    for i,s in enumerate(sample_rows):
        key=('group',s.group_type or 'unspecified',s.group_id) if s.group_id else ('sha',s.sha256 or s.sample_id)
        groups[key].append(i)
    blocks=list(groups.values())
    def calc(ix):
        return (float(f1_score(y[ix],pred[ix],labels=labels,average='macro',zero_division=0)),
                float(accuracy_score(y[ix],pred[ix])))
    vals=[]
    for _ in range(repetitions):
        chosen=rng.integers(0,len(blocks),size=len(blocks))
        ix=np.asarray([i for j in chosen for i in blocks[int(j)]],dtype=int)
        vals.append(calc(ix))
    series=np.asarray(vals)
    def ci(j):return [float(np.quantile(series[:,j],.025)),float(np.quantile(series[:,j],.975))]
    return {'macro_f1_ci95':ci(0),'accuracy_ci95':ci(1),
            'bootstrap_method':'group-cluster percentile bootstrap (unique sample/file hashes when group ID absent)',
            'bootstrap_resamples':repetitions,'bootstrap_clusters':len(blocks),
            'limitations':['Coverage of nominal confidence intervals is not guaranteed on small or correlated samples.',
                           'Unknown patient identity may mean the fallback clusters are not independent.']}

def _score(model,rows,boot_seed=42):
    if not rows:return {'error':'No evaluation rows'}
    probs=_pred(model,rows);cl=model.classes_.tolist();pred=np.asarray([cl[int(np.argmax(p))] for p in probs]);y=np.asarray([s.label for s in rows])
    labels=sorted(set(cl)|set(y.tolist()))
    acc=float(accuracy_score(y,pred));balanced=float(balanced_accuracy_score(y,pred));macro=float(f1_score(y,pred,labels=labels,average='macro',zero_division=0))
    cm=confusion_matrix(y,pred,labels=labels).tolist()
    ci=_cluster_bootstrap_metrics(y,pred,rows,labels,seed=boot_seed)
    metrics={'accuracy':acc,'balanced_accuracy':balanced,'macro_f1':macro,'confusion_matrix':cm,'labels':labels,'n':len(rows),**ci}
    metrics['per_class']=classification_report(y,pred,labels=labels,output_dict=True,zero_division=0)
    c=np.max(probs,axis=1);hit=(y==pred).astype('float32');calibration=[];ece=0.0
    for k in range(10):
        low=k/10;high=(k+1)/10
        mask=(c>=low)&(c<=high if k==9 else c<high)
        if mask.sum():
            conf=float(c[mask].mean());observed=float(hit[mask].mean());ece+=float(mask.mean())*abs(conf-observed)
            calibration.append({'lower':low,'upper':high,'mean_confidence':conf,'empirical_accuracy':observed,'n':int(mask.sum())})
    metrics['calibration_bins']=calibration;metrics['expected_calibration_error']=ece
    try:
        ix=np.array([cl.index(x) for x in y]);onehot=np.eye(len(cl))[ix]
        metrics['brier_multiclass']=float(np.mean(np.sum((probs-onehot)**2,axis=1)))
        metrics['auroc_ovr']=float(roc_auc_score(onehot,probs,average='macro',multi_class='ovr')) if len(set(y))==len(cl) and all(np.sum(onehot[:,j])>0 for j in range(len(cl))) else None
    except ValueError:metrics['brier_multiclass']=None;metrics['auroc_ovr']=None
    predictions=[]
    for i,s in enumerate(rows):
        predictions.append({'sample_id':s.sample_id,'sample_db_id':s.id,'actual':s.label,'predicted':str(pred[i]),'confidence':round(float(np.max(probs[i])),5),'correct':bool(s.label==pred[i]),'split':s.split,'site':s.site or 'unknown','group_id':s.group_id})
    subgroups=[]
    sites=defaultdict(list)
    for p in predictions:sites[p['site']].append(p)
    for site,items in sorted(sites.items()):
        if len(items)<5:subgroups.append({'name':site,'n':len(items),'metric':None,'note':'Too few records to report subgroup metric'})
        else:subgroups.append({'name':site,'n':len(items),'metric':float(np.mean([p['correct'] for p in items])),'note':'Exploratory site-level accuracy'})
    return {'metrics':metrics,'predictions':predictions,'subgroups':subgroups}

def _manifest(d,config,seed):
    try:
        revision=subprocess.run(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=2).stdout.strip() or 'not_versioned'
    except Exception:revision='unavailable'
    return {'code_revision':revision,'research_only':True,'dataset_id':d.id,'dataset_manifest_sha256':d.manifest_hash,'created_utc':now().isoformat(),
       'seed':seed,'config':config,'python':sys.version.split()[0],'platform':platform.platform(),'numpy':np.__version__,
       'scikit_learn':sklearn.__version__,'scipy':scipy.__version__,'pillow':Image.__version__ if hasattr(Image,'__version__') else 'unknown','feature_pipeline':'48px HOG + 12px RGB; logistic regression, class_weight balanced',
       'model_version':LAB_VERSION,'warning':'Not a clinically validated model. Reported accuracy is research-only.'}

def _save_model(model,experiment_id,manifest):
    dest=ARTIFACT_ROOT/experiment_id;dest.mkdir(parents=True,exist_ok=True)
    joblib.dump(model,dest/'baseline.joblib')
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

def _check_group_leakage(samples):
    groups=defaultdict(set)
    for s in samples:
        if s.group_id:groups[(s.group_type or 'unspecified',s.group_id)].add(s.split)
    return [{'group_type':k[0],'id':k[1],'splits':sorted(v)} for k,v in groups.items() if len(v)>1][:50]

def run_baseline(exp_id,progress=None):
    with Session() as db:
        e=db.get(Experiment,exp_id);d,samples=_load(db,e.dataset_id);config=jl(e.config);seed=int(config.get('seed',42))
        train=[s for s in samples if s.split=='train'];validation=[s for s in samples if s.split=='val'];test=[s for s in samples if s.split=='test']
        if not test:raise ValueError('Dataset needs a held-out test split')
        if progress:progress(15,'Extracting CPU-friendly HOG and color features')
        safe_validation,safe_test,integrity=_evaluation_integrity(train,validation,test)
        fit_train=_select_training_subset(train,seed=seed)
        model=_model(fit_train,seed)
        class_counts=Counter(s.label for s in train)
        fit_class_counts=Counter(s.label for s in fit_train)
        training_warnings=[]
        if min(class_counts.values())<3:
            training_warnings.append('Some training classes contain fewer than 3 samples. Results are highly unstable; obtain more independently labeled examples before making research claims.')
        if any(s.label not in class_counts for s in safe_test):
            training_warnings.append('Held-out test includes labels absent from training; those classes cannot be predicted by this baseline.')
        if len(safe_test)<20:
            training_warnings.append('Fewer than 20 independent test records remain after leakage screening. Performance intervals will be unstable.')
        if len(fit_train)<len(train):
            training_warnings.append('The CPU model used a deterministic class-preserving subset of training data. Source prevalence and sample coverage differ from the original training split.')
        if progress:progress(63,'Evaluating only provenance-screened validation and test partitions')
        outcome={'training_class_counts':dict(class_counts),
                 'model_fit_training_class_counts':dict(fit_class_counts),
                 'source_train_n':len(train),'model_fit_train_n':len(fit_train),
                 'training_selection_policy':'all_training_images' if len(fit_train)==len(train) else 'deterministic_class_preserving_seed_'+str(seed),
                 'training_warnings':training_warnings,'validation':_score(model,safe_validation,seed) if safe_validation else None,'test':_score(model,safe_test,seed),
           'data_quality_warnings':_check_group_leakage(samples),'evaluation_integrity':integrity,
           'train_n':len(train),'test_n':len(safe_test),'validation_n':len(safe_validation),
           'method':'Logistic regression on HOG + downsized RGB; no GPU, no diagnostic claims','baseline':True}
        manifest=_manifest(d,config,seed);manifest['group_overlap_warning']=bool(outcome['data_quality_warnings']);_save_model(model,e.id,manifest)
        outcome['manifest']=manifest
        e.result=jd(outcome);e.status='completed';e.finished_at=now();db.commit()
        if progress:progress(100,'Baseline complete')
        return outcome

def _latest_model(db,dataset_id):
    rows=db.scalars(select(Experiment).where(Experiment.dataset_id==dataset_id,Experiment.kind=='baseline',Experiment.status=='completed').order_by(Experiment.created_at.desc())).all()
    for e in rows:
        path=ARTIFACT_ROOT/e.id/'baseline.joblib'
        if path.exists():return e,joblib.load(path)
    raise ValueError('Run Model Baseline first to generate a reproducible classifier')

def run_shortcut(exp_id,progress=None):
    """Source-label association and occlusion sensitivity; neither establishes causation."""
    with Session() as db:
        e=db.get(Experiment,exp_id);d,samples=_load(db,e.dataset_id);base,model=_latest_model(db,d.id)
        train=[s for s in samples if s.split=='train']
        validation=[s for s in samples if s.split=='val']
        all_test=[s for s in samples if s.split=='test']
        if not all_test:raise ValueError('Requires test images')
        _,safe_test,integrity=_evaluation_integrity(train,validation,all_test)
        test=safe_test[:160]
        if progress:progress(20,'Testing leakage-screened control and masked images')
        def mask_features(s,kind):
            with Image.open(safe_path(s.relpath)) as im:
                im=im.convert('RGB')
                if kind=='corner_mask':
                    from PIL import ImageDraw
                    draw=ImageDraw.Draw(im);draw.rectangle((0,0,max(12,int(im.width*.14)),max(12,int(im.height*.14))),fill=tuple(int(z) for z in np.asarray(im).mean(axis=(0,1))))
                else:raise ValueError('Bad mask kind')
                tmp=ARTIFACT_ROOT/e.id/f'tmp_{s.id}.png';tmp.parent.mkdir(parents=True,exist_ok=True);im.save(tmp)
            try:return extract_features(tmp)
            finally:tmp.unlink(missing_ok=True)
        orig=_pred(model,test);masked=model.predict_proba(np.vstack([mask_features(s,'corner_mask') for s in test]))
        flip=int(np.sum(np.argmax(orig,axis=1)!=np.argmax(masked,axis=1)))
        conf_change=float(np.mean(np.abs(np.max(orig,axis=1)-np.max(masked,axis=1))))
        output={'baseline_experiment_id':base.id,'test_n':len(test),'evaluation_integrity':integrity,'region':'upper-left approximately 14% corner','prediction_flip_rate':flip/len(test),
            'mean_max_confidence_change':conf_change,'distribution_shift_test':'controlled corner masking','caveat':'Image occlusion may change important image content; changes do not prove shortcut learning. Test confounds and controls before causal claims.',
            'manifest':_manifest(d,jl(e.config),42)}
        e.result=jd(output);e.status='completed';e.finished_at=now();db.commit()
        if progress:progress(100,'Shortcut probe complete')
        return output

def _transform(im,kind,strength=0.4):
    """Controlled transformations; strength in [0,1]. Same setting recorded in manifest."""
    from PIL import ImageDraw
    strength=float(strength)
    if not np.isfinite(strength) or not (0<=strength<=1):raise ValueError('Strength must be in [0, 1]')
    im=im.convert('RGB')
    if kind=='brightness_up':return ImageEnhance.Brightness(im).enhance(1+0.625*strength)
    if kind=='brightness_down':return ImageEnhance.Brightness(im).enhance(max(0.1,1-0.625*strength))
    if kind=='blur':return im.filter(ImageFilter.GaussianBlur(radius=3.375*strength))
    if kind=='corner_mask':
        out=im.copy()
        w=max(1,int(out.width*(0.03+0.35*strength)));h=max(1,int(out.height*(0.03+0.35*strength)))
        if strength>0:ImageDraw.Draw(out).rectangle((0,0,w,h),fill=(85,85,85))
        return out
    raise ValueError('Unrecognized transform')

def run_counterfactual(exp_id,progress=None):
    with Session() as db:
        e=db.get(Experiment,exp_id);d,samples=_load(db,e.dataset_id);cfg=jl(e.config)
        requested=cfg.get('sample_id');strength=float(cfg.get('strength',0.4));
        if not np.isfinite(strength) or not (0 <= strength <= 1):raise ValueError('Strength must be between 0 and 1')
        s=next((s for s in samples if s.id==requested or s.sample_id==requested),None)
        if not s:raise ValueError('Select a sample to test')
        base,model=_latest_model(db,d.id)
        orig=_pred(model,[s])[0];labels=model.classes_.tolist();variants=[]
        dest=ARTIFACT_ROOT/e.id/'variants';dest.mkdir(parents=True,exist_ok=True)
        for i,kind in enumerate(['brightness_up','brightness_down','blur','corner_mask']):
            if progress:progress(15+int(i*19),f'Running {kind}')
            with Image.open(safe_path(s.relpath)) as im:mod=_transform(im,kind,strength)
            path=dest/f'{kind}.png';mod.save(path)
            p=model.predict_proba(np.vstack([extract_features(path)]))[0]
            variants.append({'name':kind,'predicted':labels[int(np.argmax(p))],'confidence':float(np.max(p)),
                'changed_prediction':bool(np.argmax(orig)!=np.argmax(p)),'confidence_delta':float(np.max(p)-np.max(orig)),
                'image_path':f'{e.id}/variants/{kind}.png'})
        out={'sample_id':s.id,'recorded_label':s.label,'baseline_experiment_id':base.id,
          'original_prediction':labels[int(np.argmax(orig))],'original_confidence':float(np.max(orig)),
          'strength':strength,'transform_policy':'Four predefined transforms at recorded strength',
          'variants':variants,'caveat':'Controlled transforms reveal output sensitivity, not medical diagnosis or counterfactual causality.',
          'manifest':_manifest(d,cfg,42)}
        e.result=jd(out);e.status='completed';e.finished_at=now();db.commit()
        if progress:progress(100,'Counterfactual study complete')
        return out

def run_cross_dataset(exp_id,progress=None):
    with Session() as db:
        e=db.get(Experiment,exp_id);d,samples=_load(db,e.dataset_id);cfg=jl(e.config)
        target_id=cfg.get('target_dataset_id')
        if not target_id or target_id==d.id:raise ValueError('Choose a separate target dataset')
        target,external=_load(db,target_id);base,model=_latest_model(db,d.id)
        source_provenance=(d.name+' '+d.source).lower()
        target_provenance=(target.name+' '+target.source).lower()
        if ('ham10000' in source_provenance and 'dermamnist' in target_provenance) or ('dermamnist' in source_provenance and 'ham10000' in target_provenance):
            raise ValueError('DermaMNIST is derived from HAM10000 and cannot be treated as an independent external dataset')
        if cfg.get('independence_confirmed') is not True:
            raise ValueError('Researcher must confirm that the target is independently collected and is not a subset, resize, augmentation or re-export of the source dataset')
        source_classes=set(str(x) for x in model.classes_.tolist())
        target_classes=set(str(s.label) for s in external)
        if d.modality!=target.modality:
            raise ValueError('Different declared modalities; cross-dataset evaluation is blocked')
        supplied_mapping=cfg.get('target_label_mapping')
        if supplied_mapping is None:
            if source_classes!=target_classes:
                raise ValueError('Incompatible label vocabularies: provide an explicit one-to-one target-to-source label mapping')
            label_mapping={label:label for label in target_classes}
            mapping_confirmed=False
        else:
            if cfg.get('label_mapping_confirmed') is not True:
                raise ValueError('Explicit class mapping has not been confirmed by the researcher')
            if not isinstance(supplied_mapping,dict):
                raise ValueError('Target label mapping must be a JSON object')
            label_mapping={str(k):str(v) for k,v in supplied_mapping.items()}
            if set(label_mapping)!=target_classes:
                raise ValueError('Label mapping must include every decodable target class exactly once')
            if set(label_mapping.values())!=source_classes or len(set(label_mapping.values()))!=len(label_mapping):
                raise ValueError('Label mapping must map one-to-one onto every source model class')
            mapping_confirmed=True
        source_hashes={x.sha256 for x in samples if x.sha256}
        overlaps=sum(x.sha256 in source_hashes for x in external if x.sha256)
        if overlaps:
            raise ValueError(f'Cross-dataset comparison blocked: {overlaps} target images share exact file hashes with the source dataset')
        if progress:progress(15,'Screening decoded image identities across datasets')
        from .analysis_engine import pixel_fingerprint
        def image_identity(sample):
            return sample.pixelhash or pixel_fingerprint(safe_path(sample.relpath))
        source_pixels={image_identity(x) for x in samples}
        duplicate_pixels=sum(image_identity(x) in source_pixels for x in external)
        if duplicate_pixels:
            raise ValueError(f'Cross-dataset comparison blocked: {duplicate_pixels} target images match decoded source pixels, including possible re-encodings')
        test=[s for s in external if s.split=='test'][:500]
        if not test:raise ValueError('Target dataset needs a decodable test partition')
        mapped_test=[SimpleNamespace(
            id=s.id,sample_id=s.sample_id,label=label_mapping[str(s.label)],split=s.split,
            site=s.site,group_id=s.group_id,group_type=s.group_type,relpath=s.relpath,
            sha256=s.sha256
        ) for s in test]
        if progress:progress(25,'Evaluating frozen model on external images')
        outcome={'source_dataset_id':d.id,'target_dataset_id':target_id,'base_experiment_id':base.id,
            'external_test':_score(model,mapped_test,42),'label_mapping':label_mapping,
            'label_mapping_confirmed':mapping_confirmed,
            'license_notice':target.license,'comparison_limits':['Matching text labels and modality do not prove clinical equivalence.','Any explicit class mapping must be justified from the dataset documentation and independently reviewed.','Byte-for-byte and decoded-pixel identity checks cannot establish patient independence or rule out near duplicates.','Dataset shift may reflect confounding or differences in labels or acquisition.'],'manifest':_manifest(d,cfg,42)}
        e.result=jd(outcome);e.status='completed';e.finished_at=now();db.commit()
        if progress:progress(100,'Cross-dataset evaluation complete')
        return outcome


IMPACT_FINDING_KINDS=frozenset({
    'split_leakage','group_overlap','exact_duplicate','pixel_duplicate','near_duplicate','label_suspicion'
})

def _impact_exclusion_ids(db,d,train):
    train_ids={sample.id for sample in train}
    confirmed=db.scalars(select(Finding).where(
        Finding.dataset_id==d.id,Finding.status=='confirmed'
    )).all()
    exclusions=set()
    for finding in confirmed:
        if finding.kind not in IMPACT_FINDING_KINDS:
            continue
        for sample_id in (finding.sample_id,finding.linked_id):
            if sample_id and sample_id in train_ids:
                exclusions.add(sample_id)
    return exclusions,confirmed

def _impact_readiness(db,d,samples):
    train=[sample for sample in samples if sample.split=='train']
    test=[sample for sample in samples if sample.split=='test']
    exclusions,confirmed=_impact_exclusion_ids(db,d,train)
    supported_confirmed=[finding for finding in confirmed
        if finding.kind in IMPACT_FINDING_KINDS and
        (finding.sample_id in {s.id for s in train} or finding.linked_id in {s.id for s in train})]
    suspected=db.scalars(select(Finding).where(
        Finding.dataset_id==d.id,Finding.status=='suspected',
        Finding.kind.in_(IMPACT_FINDING_KINDS)
    )).all()
    train_ids={sample.id for sample in train}
    suspected_train_ids={sid for finding in suspected
        for sid in (finding.sample_id,finding.linked_id) if sid and sid in train_ids}
    audit=db.scalar(select(AuditRun).where(
        AuditRun.dataset_id==d.id,AuditRun.status=='completed'
    ).order_by(AuditRun.created_at.desc()).limit(1))
    curated=[sample for sample in train if sample.id not in exclusions]
    fit_train=_select_training_subset(train,seed=42)
    fit_ids={sample.id for sample in fit_train}
    fit_exclusions=exclusions & fit_ids
    fit_curated=[sample for sample in fit_train if sample.id not in exclusions]
    reasons=[]
    if not audit:
        reasons.append('Run a completed Forensic Audit before using the Impact Simulator.')
    if not test:
        reasons.append('A held-out test split is required and must remain unchanged.')
    if not exclusions:
        reasons.append('No reviewer-confirmed supported finding is linked to a training image. In Review Center, inspect an image-linked finding and confirm it only if its evidence supports the concern.')
    if len(curated)<20 or len({sample.label for sample in curated})<2:
        if exclusions:
            reasons.append('Removing the confirmed training records would leave fewer than 20 images or fewer than 2 classes.')
    if exclusions and not fit_exclusions:
        reasons.append('The confirmed records are outside the deterministic 2,400-image CPU training subset. A different documented sampling plan is required.')
    if fit_exclusions and (len(fit_curated)<20 or len({sample.label for sample in fit_curated})<2):
        reasons.append('Removing the confirmed records would leave too few images or classes in the CPU model-fit subset.')
    return {
        'ready':not reasons,'reasons':reasons,
        'audit_completed':bool(audit),
        'train_count':len(train),'test_count':len(test),
        'curated_train_count':len(curated),
        'confirmed_supported_findings':len(supported_confirmed),
        'confirmed_training_samples':len(exclusions),
        'suspected_training_samples':len(suspected_train_ids),
        'other_confirmed_findings':max(0,len(confirmed)-len(supported_confirmed)),
        'supported_finding_kinds':sorted({finding.kind for finding in supported_confirmed}),
        'model_fit_train_count':len(fit_train),
        'confirmed_exclusions_in_model_fit':len(fit_exclusions),
        'note':'Only reviewer-confirmed, supported image-linked findings that point to the training split can be excluded. Labels and original images are never overwritten.'
    }

def impact_readiness(db,dataset_id):
    d,samples=_load(db,dataset_id)
    return _impact_readiness(db,d,samples)

def run_impact(exp_id,progress=None):
    """Removal-only ablation of REVIEW-CONFIRMED training findings, never alters reference dataset."""
    with Session() as db:
        e=db.get(Experiment,exp_id);d,samples=_load(db,e.dataset_id);cfg=jl(e.config)
        train=[s for s in samples if s.split=='train'];test=[s for s in samples if s.split=='test']
        if not test:raise ValueError('A fixed test split is required')
        readiness=_impact_readiness(db,d,samples)
        if not readiness['ready']:
            raise ValueError('Impact Simulator is not ready: '+' '.join(readiness['reasons']))
        exclusions,_=_impact_exclusion_ids(db,d,train)
        curated=[s for s in train if s.id not in exclusions]
        validation=[s for s in samples if s.split=='val']
        _,safe_test,integrity=_evaluation_integrity(train,validation,test)
        if progress:progress(18,'Training original baseline on fixed training split')
        fit_train=_select_training_subset(train,seed=42)
        removed_from_fit=[s for s in fit_train if s.id in exclusions]
        if not removed_from_fit:
            raise ValueError('The confirmed training exclusions are absent from the capped model-fit subset. Select a larger training cap or different documented sampling plan before the impact comparison.')
        fit_curated=[s for s in fit_train if s.id not in exclusions]
        if len(fit_curated)<20 or len({s.label for s in fit_curated})<2:
            raise ValueError('Removing confirmed findings from the fixed model training subset leaves too few images or classes')
        m0=_model(fit_train,42);first=_score(m0,safe_test,42)
        if progress:progress(60,'Training removal-only ablation on curated training split')
        m1=_model(fit_curated,42);second=_score(m1,safe_test,42)
        # Paired resampling preserves correlations between the two predictions.
        y=np.asarray([s.label for s in safe_test]);labs=sorted(set(y.tolist())|set(m0.classes_.tolist())|set(m1.classes_.tolist()))
        p0=np.asarray([m0.classes_[int(np.argmax(p))] for p in _pred(m0,safe_test)])
        p1=np.asarray([m1.classes_[int(np.argmax(p))] for p in _pred(m1,safe_test)])
        grouped=defaultdict(list)
        for i,sample in enumerate(safe_test):
            key=('group',sample.group_type or 'unspecified',sample.group_id) if sample.group_id else ('sha',sample.sha256 or sample.sample_id)
            grouped[key].append(i)
        blocks=list(grouped.values());rng=np.random.default_rng(42);deltas=[]
        for _ in range(300):
            selection=rng.integers(0,len(blocks),size=len(blocks))
            ix=np.asarray([i for j in selection for i in blocks[int(j)]],dtype=int)
            deltas.append(float(f1_score(y[ix],p1[ix],labels=labs,average='macro',zero_division=0)-f1_score(y[ix],p0[ix],labels=labs,average='macro',zero_division=0)))
        delta_ci=[float(np.quantile(deltas,.025)),float(np.quantile(deltas,.975))]
        # Persist an immutable derived metadata version; source images remain in place.
        version=Dataset(name=(d.name+' · reviewed exclusion')[:200],source='Derived reviewer-confirmed training exclusion',source_url=d.source_url,license=d.license,
          modality=d.modality,description='Research-only immutable removal ablation version; labels and pixels unchanged.',synthetic=d.synthetic,parent_id=d.id,
          meta=jd({'excluded_train_sample_ids':sorted(exclusions),'experiment_id':e.id,'parent_dataset_id':d.id}))
        db.add(version);db.flush()
        new_samples=[]
        for s in samples:
            if s.id in exclusions and s.split=='train':continue
            new_samples.append(Sample(dataset_id=version.id,sample_id=s.sample_id,relpath=s.relpath,label=s.label,split=s.split,group_id=s.group_id,group_type=s.group_type,
               site=s.site,source_id=s.source_id,sha256=s.sha256,pixelhash=s.pixelhash,phash=s.phash,width=s.width,height=s.height,
               meta=jd({'derived_from_sample_id':s.id,'remediation':'excluded confirmed training concern'})))
        db.add_all(new_samples);version.manifest_hash=manifest_hash(new_samples)
        output={'derived_dataset_id':version.id,'removed_train_sample_ids':sorted(exclusions),'removed_count':len(exclusions),'original_train_n':len(train),'curated_train_n':len(curated),
           'original_model_fit_train_n':len(fit_train),'curated_model_fit_train_n':len(fit_curated),
           'removed_from_model_fit_n':len(removed_from_fit),
           'model_fit_selection_policy':'fixed_deterministic_class_preserving_seed_42',
           'evaluation_test_ids_sha256':hashlib.sha256('|'.join(sorted(x.sample_id for x in safe_test)).encode()).hexdigest(),
           'evaluation_integrity':integrity,'paired_macro_f1_delta_ci95':delta_ci,
           'before':first['metrics'],'after':second['metrics'],
           'macro_f1_delta':second['metrics']['macro_f1']-first['metrics']['macro_f1'],
           'manifest':_manifest(d,cfg,42),
           'limitations':['This is a small-sample removal-only ablation, not evidence of causality or clinical benefit.','Potential confirmation and selection bias from human-reviewed findings.','Test cohort is reused for reporting only; never optimize remediation using test results.']}
        e.result=jd(output);e.status='completed';e.finished_at=now();db.commit()
        if progress:progress(100,'Impact ablation complete')
        return output

def run_scenario(exp_id,progress=None):
    """Create new immutable metadata+image version with a bounded number of known label corruptions."""
    with Session() as db:
        e=db.get(Experiment,exp_id);source,samples=_load(db,e.dataset_id);cfg=jl(e.config)
        if len(samples)<20:raise ValueError('Need at least 20 images')
        seed=int(cfg.get('seed',42));rate=float(cfg.get('label_flip_rate',.08))
        if not np.isfinite(rate) or not .01<=rate<=.3:raise ValueError('Flip rate 0.01–0.30')
        labels=sorted(set(s.label for s in samples))
        if len(labels)<2:raise ValueError('At least 2 classes required')
        rng=random.Random(seed);train=[s for s in samples if s.split=='train'];choices=rng.sample(train,max(1,int(len(train)*rate)))
        selected={s.id for s in choices}
        new=Dataset(name=(source.name+' · scenario '+str(seed))[:200],source='Derived controlled fault scenario',source_url=source.source_url,license=source.license,
            modality=source.modality,description='Immutable synthetic label-corruption version. Never modify source data.',synthetic=True,parent_id=source.id,meta=jd({'injected_label_error_rate':rate,'seed':seed,'original_dataset_id':source.id}))
        db.add(new);db.flush();copies=[];truth=[]
        for s in samples:
            label=s.label
            if s.id in selected:
                label=labels[(labels.index(label)+1)%len(labels)]
                truth.append({'source_sample_id':s.sample_id,'before':s.label,'after':label})
            copies.append(Sample(dataset_id=new.id,sample_id=s.sample_id,relpath=s.relpath,label=label,split=s.split,group_id=s.group_id,group_type=s.group_type,site=s.site,source_id=s.source_id,sha256=s.sha256,pixelhash=s.pixelhash,phash=s.phash,width=s.width,height=s.height,meta=jd({'derived_from_sample_id':s.id,'injected_label_change':s.id in selected})))
        db.add_all(copies);new.manifest_hash=manifest_hash(copies)
        dest=ARTIFACT_ROOT/e.id;dest.mkdir(parents=True,exist_ok=True)
        (dest/'synthetic_truth.json').write_text(json.dumps({'changes':truth,'generated_from':source.id},indent=2),encoding='utf-8')
        outcome={'derived_dataset_id':new.id,'source_dataset_id':source.id,'injected_label_flips':len(truth),'total_samples':len(copies),'truth_artifact':f'{e.id}/synthetic_truth.json','manifest':_manifest(source,cfg,seed),'caveat':'These are artificial label defects with known truth; not observed medical mislabels.'}
        e.result=jd(outcome);e.status='completed';e.finished_at=now();db.commit()
        if progress:progress(100,'Scenario dataset version saved')
        return outcome

EXPERIMENT_RUNNERS={'baseline':run_baseline,'shortcut':run_shortcut,'counterfactual':run_counterfactual,'cross_dataset':run_cross_dataset,'impact':run_impact,'scenario':run_scenario}
