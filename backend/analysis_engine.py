"""Auditable, CPU-bounded forensic detectors. Suspicions are NOT clinical ground truth."""
from __future__ import annotations
from collections import Counter,defaultdict
from itertools import combinations
import hashlib,math,os,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageEnhance,ImageFilter
from scipy.fft import dctn
from scipy.stats import chi2_contingency
from sqlalchemy import select,delete
from skimage.metrics import structural_similarity as ssim
from skimage.feature import hog
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold,StratifiedGroupKFold
from sklearn.metrics import f1_score,balanced_accuracy_score,accuracy_score,confusion_matrix,classification_report
from .db import Session,Dataset,Sample,Finding,AuditRun,now,jd,jl,uid
from .security import safe_path,sha_file,image_info

DETECTOR_VERSION='mdf-0.8.0'
KIND_COST={'exact_duplicate':0.6,'pixel_duplicate':0.6,'split_leakage':0.9,'group_overlap':0.8,'near_duplicate':1.2,'label_suspicion':1.7,'integrity':0.5,'source_association':1.3}
SEVERITY={'critical':1.,'high':.8,'medium':.55,'low':.3}

def phash_image(path):
    with Image.open(path) as im:
        ar=np.asarray(im.convert('L').resize((32,32),Image.Resampling.LANCZOS),dtype=np.float32)
    arr=dctn(ar,type=2,norm='ortho')[:8,:8]
    med=np.median(arr[1:,:]);bits=(arr>med).flatten();return ''.join(f'{int("".join(str(int(z)) for z in bits[k:k+4]),2):x}' for k in range(0,64,4))

def pixel_fingerprint(path):
    with Image.open(path) as im:
        rgb=im.convert('RGB');return hashlib.sha256(f'{rgb.width}x{rgb.height}'.encode()+rgb.tobytes()).hexdigest()

def hamm(a,b):return (int(a,16)^int(b,16)).bit_count()

def similarity(p1,p2):
    with Image.open(p1) as a,Image.open(p2) as b:
        x=np.asarray(a.convert('L').resize((96,96)),dtype=np.float32)
        y=np.asarray(b.convert('L').resize((96,96)),dtype=np.float32)
    return float(ssim(x,y,data_range=255))

def extract_features(path):
    """A reproducible, lightweight CPU baseline—not a medical diagnostic model."""
    with Image.open(path) as im:
        rgb=np.asarray(im.convert('RGB').resize((48,48)),dtype=np.float32)/255
    gray=np.asarray(Image.fromarray((rgb*255).astype('uint8')).convert('L'),dtype=np.float32)/255
    h=hog(gray,pixels_per_cell=(8,8),cells_per_block=(2,2),feature_vector=True,block_norm='L2-Hys')
    small=np.asarray(Image.fromarray((rgb*255).astype('uint8')).resize((12,12)),dtype=np.float32).flatten()/255
    return np.concatenate([h,small]).astype('float32')

def create_finding(run,dataset,kind,title,detail,sample=None,linked=None,confidence=.5,severity='medium',evidence=None):
    confidence=max(0.,min(1.,float(confidence)))
    ev=evidence or {}
    ev.update({'detector_version':DETECTOR_VERSION,'limitation':'Automated finding for human review; not a verified medical conclusion.'})
    return Finding(dataset_id=dataset.id,audit_id=run.id,kind=kind,title=title,detail=detail,sample_id=sample.id if sample else None,linked_id=linked.id if linked else None,confidence=confidence,severity=severity,evidence=jd(ev),detector=DETECTOR_VERSION,cost=KIND_COST.get(kind,1.))

def audit(dataset_id,run_id,progress=None):
    def tell(n,msg):
        if progress: progress(n,msg)
    with Session() as db:
        dataset=db.get(Dataset,dataset_id); run=db.get(AuditRun,run_id)
        if not dataset or not run:raise ValueError('Missing dataset or audit')
        samples=db.scalars(select(Sample).where(Sample.dataset_id==dataset_id).order_by(Sample.sample_id)).all()
        if not samples:raise ValueError('Dataset contains no samples')
        findings=[];valid=[]
        # Audit results are immutable at run level; avoid duplicate findings on retry.
        db.execute(delete(Finding).where(Finding.audit_id==run_id))
        db.commit()  # release SQLite write lock before worker reports progress in another session
        seen_ids={};bucket_sha=defaultdict(list);bucket_px=defaultdict(list);bucket_group=defaultdict(list)
        tell(3,'Verifying source images and identifiers')
        for i,s in enumerate(samples):
            if not (s.label or '').strip():
                findings.append(create_finding(run,dataset,'integrity','Missing recorded label','The source record has an empty classification label.',s,None,1.0,'high',{'field':'label'}))
            if s.sample_id in seen_ids:
                findings.append(create_finding(run,dataset,'integrity','Repeated sample identifier','The same sample identifier occurs more than once.',s,seen_ids[s.sample_id],1.,'high',{'sample_id':s.sample_id}))
            else:seen_ids[s.sample_id]=s
            try:
                p=safe_path(s.relpath);width,height=image_info(p)
                s.width=width;s.height=height
                s.sha256=sha_file(p);s.pixelhash=pixel_fingerprint(p);s.phash=phash_image(p)
                bucket_sha[s.sha256].append(s);bucket_px[s.pixelhash].append(s)
                if s.group_id:bucket_group[(s.group_type or 'unspecified',s.group_id)].append(s)
                valid.append(s)
            except (ValueError,OSError) as exc:
                findings.append(create_finding(run,dataset,'integrity','Unreadable or unsafe image',str(exc)[:320],s,None,1.,'high',{'path_id':s.sample_id,'status':'decode_failed'}))
            if i%100==0: tell(4+int(18*i/max(1,len(samples))),f'Validated {i+1}/{len(samples)} images')
        dimension_counts=Counter((s.width,s.height) for s in valid)
        if dimension_counts:
            dominant,count=dimension_counts.most_common(1)[0]
            if count/max(1,len(valid))>=.80:
                for s in valid:
                    if (s.width,s.height)!=dominant:
                        findings.append(create_finding(run,dataset,'integrity','Uncommon image dimensions',
                            f'This image is {s.width}×{s.height}; the dataset majority is {dominant[0]}×{dominant[1]}. Different sizes can be entirely valid.',s,None,.6,'low',
                            {'expected_common_width':dominant[0],'expected_common_height':dominant[1],'actual_width':s.width,'actual_height':s.height,'conclusion':'investigate, do not classify as corrupted'}))
        tell(25,'Checking exact duplicates and group overlap')
        pairs_seen=set()
        def emit_pairs(groups,kind,confidence):
            for bucket in groups.values():
                if len(bucket)<2:continue
                # cap a massive duplicate family; disclose truncation in summary
                for a,b in list(combinations(bucket[:30],2))[:150]:
                    key=tuple(sorted([a.id,b.id]));
                    if key in pairs_seen:continue
                    pairs_seen.add(key)
                    different=a.split!=b.split
                    title=('Cross-split ' if different else '')+('exact image duplicate' if kind!='pixel_duplicate' else 'pixel-identical images')
                    findings.append(create_finding(run,dataset,'split_leakage' if different else kind,title,
                        f'{a.sample_id} ({a.split}) and {b.sample_id} ({b.split}) share matching image content.',a,b,confidence,'critical' if different else 'medium',
                        {'evidence_type':'sha256' if kind=='exact_duplicate' else 'pixel_sha256','same_image':True,'cross_split':different,'hash':(a.sha256 if kind=='exact_duplicate' else a.pixelhash)}))
        emit_pairs(bucket_sha,'exact_duplicate',1.)
        emit_pairs(bucket_px,'pixel_duplicate',1.)
        for (_,gid),bucket in bucket_group.items():
            splits=sorted(set(x.split for x in bucket))
            if len(splits)>1:
                a=next(x for x in bucket if x.split==splits[0]);b=next(x for x in bucket if x.split!=splits[0]);typ=a.group_type or 'unspecified'
                findings.append(create_finding(run,dataset,'group_overlap','Group identifier overlaps across splits',
                    f'{typ} group {gid} appears in {", ".join(splits)}. Group IDs alone do not prove patient identity.',a,b,1.,'high',{'group_id':gid,'group_type':typ,'split_names':splits,'evidence_type':'matching_group_identifier'}))
        tell(42,'Retrieving perceptual-neighbor candidates')
        # LSH candidate retrieval: 8 disjoint 8-bit blocks; if <=7 bit errors, some block matches.
        buckets=defaultdict(list)
        for s in valid:
            for k in range(8):buckets[(k,(int(s.phash,16)>>(8*k))&255)].append(s)
        tested=set(); max_candidates=6500;max_near=250; candidates=0;near=0
        for b in buckets.values():
            for a,c in combinations(b[:120],2):
                key=tuple(sorted([a.id,c.id]));
                if key in tested:continue
                tested.add(key)
                if key in pairs_seen or a.pixelhash==c.pixelhash:continue
                if candidates>=max_candidates or near>=max_near:break
                candidates+=1;delta=hamm(a.phash,c.phash)
                if delta>7:continue
                score=similarity(safe_path(a.relpath),safe_path(c.relpath))
                if score<.935:continue
                near+=1
                findings.append(create_finding(run,dataset,'near_duplicate','Potential near-duplicate images',
                    f'Perceptual hash distance {delta}; normalized SSIM {score:.3f}. Similarity is not proof of common patient/source.',a,c,min(.99,score),'high' if a.split!=c.split else 'medium',
                    {'phash_distance':delta,'ssim_96px':round(score,5),'cross_split':a.split!=c.split,'threshold_phash':7,'threshold_ssim':.935,'candidate_generation':'8-block LSH'}))
            if candidates>=max_candidates or near>=max_near:break
        tell(64,'Evaluating optional label and source patterns')
        # Training-only cross-fit label disagreement; bounded CPU budget.
        train=[s for s in valid if s.split=='train']; sample_limit=1600
        train=train[:sample_limit]
        labels=[x.label for x in train]
        train_label_summary={'evaluated':0,'limitations':[]}
        if len(train)>=30 and len(set(labels))>=2 and min(Counter(labels).values())>=4:
            try:
                xx=np.vstack([extract_features(safe_path(s.relpath)) for s in train])
                yy=np.asarray(labels)
                groups=np.asarray([x.group_id or x.id for x in train])
                use_group=any(s.group_id for s in train) and len(set(groups))>=6
                folds=StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=42) if use_group else StratifiedKFold(n_splits=3,shuffle=True,random_state=42)
                classes=sorted(set(labels));ci={lab:i for i,lab in enumerate(classes)}
                proba=np.zeros((len(train),len(classes)),dtype='float64')
                for tr,va in folds.split(xx,yy,groups if use_group else None):
                    if len(set(yy[tr]))<len(classes):raise ValueError('Fold missing classes; cannot estimate out-of-fold probabilities')
                    model=LogisticRegression(max_iter=250,random_state=42,class_weight='balanced',solver='liblinear')
                    model.fit(xx[tr],yy[tr]);fold_p=model.predict_proba(xx[va]);
                    for j,lab in enumerate(model.classes_):proba[va,ci[lab]]=fold_p[:,j]
                truth_p=np.asarray([proba[i,ci[lab]] for i,lab in enumerate(labels)])
                score_method='out_of_fold_label_probability'
                quality=truth_p.copy()
                try:
                    from cleanlab.rank import get_label_quality_scores
                    label_int=np.asarray([ci[z] for z in labels],dtype=int)
                    quality=np.asarray(get_label_quality_scores(labels=label_int,pred_probs=proba,method='self_confidence'),dtype=float)
                    score_method='cleanlab_self_confidence'
                except ImportError:
                    train_label_summary['cleanlab']='Not installed; ordinary OOF label probability used'
                order=np.argsort(quality)
                for j in order[:min(50,max(5,len(train)//12))]:
                    s=train[int(j)];pred=classes[int(np.argmax(proba[j]))]
                    if pred==s.label and quality[j]>=.4:continue
                    findings.append(create_finding(run,dataset,'label_suspicion','Potential label inconsistency',
                        f'Out-of-fold baseline supports the recorded label with probability {truth_p[j]:.2f}. This is not an expert label adjudication.',s,None,float(1-quality[j]),'medium',
                        {'observed_label':s.label,'model_top_label':pred,'out_of_fold_label_probability':round(float(truth_p[j]),6),'label_quality_score':round(float(quality[j]),6),'label_quality_method':score_method,'trained_on':'training split only','folds':3,'group_aware':use_group,'feature_extractor':'HOG + 12x12 RGB'}))
                train_label_summary={'evaluated':len(train),'group_aware':use_group,'label_quality_method':score_method,'limitations':['Training-only out-of-fold disagreements are not proof of labeling error.']}
            except Exception as exc:train_label_summary={'evaluated':0,'limitations':[f'Not evaluated: {type(exc).__name__}: {str(exc)[:150]}']}
        else:train_label_summary={'evaluated':0,'limitations':['Needs >=30 train images, >=2 classes and >=4/class.']}
        # Simple source vs label association, testing not causal.
        site_rows=[s for s in valid if s.site]
        if len(site_rows)>=30 and len(set(s.site for s in site_rows))>=2 and len(set(s.label for s in site_rows))>=2:
            sites=sorted(set(s.site for s in site_rows));classes=sorted(set(s.label for s in site_rows))
            if len(sites)<=20 and len(classes)<=30:
                tab=np.zeros((len(sites),len(classes)),dtype=int)
                for s in site_rows:tab[sites.index(s.site),classes.index(s.label)]+=1
                chi2,p,_,expected=chi2_contingency(tab)
                if p<.05:
                    n=tab.sum();v=math.sqrt(float(chi2)/(n*max(1,min(len(sites)-1,len(classes)-1))))
                    findings.append(create_finding(run,dataset,'source_association','Source and label are statistically associated',
                        f'Observed source-label association (Cramér V={v:.2f}, p={p:.3g}); this is not proof of shortcut learning.',None,None,min(.95,v+.2),'medium',
                        {'sites':sites,'classes':classes,'contingency':tab.tolist(),'chi2':float(chi2),'p_value':float(p),'cramers_v':v,'caveat':'Exploratory test, no multiple-testing correction required for one prespecified test. Correlation is not causation.'}))
        tell(85,'Ranking findings and preserving audit evidence')
        # Experimental heuristic IGAT: not fitted / not validated; priority freezes at audit time.
        centrality=Counter([x.sample_id for x in findings if x.sample_id]+[x.linked_id for x in findings if x.linked_id])
        for f in findings:
            importance=min(1., (centrality.get(f.sample_id,0)+centrality.get(f.linked_id,0))/8)
            f.priority=round(.45*f.confidence+.38*SEVERITY[f.severity]+.17*importance-.10*min(1,f.cost/2),5)
        db.add_all(findings)
        counts=dict(Counter(f.kind for f in findings))
        run.status='completed';run.finished_at=now();run.summary=jd({'total_findings':len(findings),'by_kind':counts,'total_samples':len(samples),'valid_samples':len(valid),'label_analysis':train_label_summary,'near_duplicate_search':{'candidate_limit':max_candidates,'candidates_tested':candidates,'candidate_limit_reached':candidates>=max_candidates,'findings_cap_reached':near>=max_near},'limitations':['Near-duplicate retrieval is thresholded, capped and approximate.','No finding should be treated as a confirmed medical label error without expert review.','Source association is exploratory and not causal.']})
        db.commit()
        tell(100,'Audit complete')
        return jl(run.summary)


def forensic_graph(db,dataset_id,limit=100):
    latest=db.scalar(select(AuditRun.id).where(AuditRun.dataset_id==dataset_id,AuditRun.status=='completed').order_by(AuditRun.created_at.desc()).limit(1))
    findings=db.scalars(select(Finding).where(Finding.audit_id==latest).order_by(Finding.priority.desc()).limit(limit)).all() if latest else []
    selected_ids={v for f in findings for v in [f.sample_id,f.linked_id] if v}
    samples=db.scalars(select(Sample).where(Sample.id.in_(selected_ids))).all() if selected_ids else []
    nodes=[{'id':'s:'+s.id,'label':s.sample_id,'type':'sample','split':s.split,'group':s.group_id} for s in samples]
    links=[]
    for f in findings:
        nodes.append({'id':'f:'+f.id,'label':f.kind.replace('_',' '),'type':'finding','status':f.status,'severity':f.severity})
        if f.sample_id:links.append({'source':'f:'+f.id,'target':'s:'+f.sample_id})
        if f.linked_id:links.append({'source':'f:'+f.id,'target':'s:'+f.linked_id})
    return {'nodes':nodes,'edges':links,'truncated':len(findings)>=limit,'note':'Connections indicate reported forensic evidence, not verified patient identity.'}


def ranking_comparison(db,dataset_id,budget=15):
    latest=db.scalar(select(AuditRun.id).where(AuditRun.dataset_id==dataset_id,AuditRun.status=='completed').order_by(AuditRun.created_at.desc()).limit(1))
    findings=db.scalars(select(Finding).where(Finding.audit_id==latest)).all() if latest else []
    if not findings:return {'strategies':[],'message':'Run an audit first.'}
    dataset=db.get(Dataset,dataset_id)
    truth=None
    if dataset.synthetic:
        p=safe_path(f'{dataset_id}/synthetic_truth.json')
        if p.exists():
            import json
            truth=json.loads(p.read_text())
    sample_ids={s.id:s.sample_id for s in db.scalars(select(Sample).where(Sample.dataset_id==dataset_id))}
    def correct(f):
        if truth is None:return None
        a=sample_ids.get(f.sample_id);b=sample_ids.get(f.linked_id)
        pairs=[set(x) for x in truth.get('exact_duplicate',[])+truth.get('near_duplicate',[])]
        if f.kind in ('split_leakage','near_duplicate','pixel_duplicate','exact_duplicate'):
            return int({a,b} in pairs)
        if f.kind=='label_suspicion':return int(a in truth.get('label_flip',[]))
        if f.kind=='group_overlap':return int(jl(f.evidence).get('group_id') in truth.get('group_overlap',[]))
        return 0
    ranked={
      'IGAT (experimental)':sorted(findings,key=lambda f:(-f.priority,f.id)),
      'Confidence':sorted(findings,key=lambda f:(-f.confidence,f.id)),
      'Severity':sorted(findings,key=lambda f:(-SEVERITY[f.severity],f.id)),
      'Random (seed 42)':sorted(findings,key=lambda f:hashlib.sha256(('42'+f.id).encode()).hexdigest()),
    }
    budget=max(1,min(budget,len(findings)))
    results=[]
    for name,order in ranked.items():
        top=order[:budget]
        results.append({'name':name,'review_budget':budget,'confirmed_known_defects':sum(correct(f) for f in top) if truth is not None else None,'total_candidates':len(findings),'ranking_ids':[f.id for f in top]})
    return {'strategies':results,'ground_truth_available':truth is not None,'caveat':'Only the deliberately injected synthetic truth is scored. This is a software sanity test, not a clinical validation or generalization claim.' if truth else 'Without independently confirmed ground truth, strategies cannot be scored for actual issue discovery.'}
