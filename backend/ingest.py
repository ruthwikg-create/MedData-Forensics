"""Dataset sources: inspectable synthetic research phantom, MedMNIST NPZ, or ZIP+CSV."""
from __future__ import annotations
import csv, io, os, shutil, zipfile, hashlib, json, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from sqlalchemy import select
from .db import DATA_ROOT,Session,Dataset,Sample,uid,jd
from .security import image_info,sha_file,safe_path,MAX_ARCHIVE_BYTES,MAX_NPZ_BYTES,ALLOWED_EXT,manifest_hash

SUPPORTED_MODALITIES=frozenset({
    'Dermatoscopic / skin lesion images','Histopathology / microscopy',
    'Radiology / X-ray','Ultrasound','MRI','CT',
    'Fundus / retinal images','Other / unspecified'
})

DEMO_LABELS=['pattern_a','pattern_b']  # explicitly synthetic and nonmedical

def _dataset(name,source,license,modality,description,synthetic=False,metadata=None,parent_id=None):
    d=Dataset(name=name[:200],source=source[:255],license=license[:250],modality=modality[:120],description=description,synthetic=synthetic,meta=jd(metadata or {}),parent_id=parent_id)
    return d

def demo_dataset(seed=42,count=128):
    """Generates synthetic geometric phantoms with known planted duplicate/leak and label flips."""
    if count<40 or count>1200: raise ValueError('Demo count must be 40–1200')
    rng=np.random.default_rng(seed); py_rng=random.Random(seed)
    with Session() as db:
        d=_dataset('Forensic training sandbox', 'Generated locally / seed '+str(seed), 'CC0 — newly generated synthetic patterns', 'Synthetic geometry (NOT medical images)',
          'Artificial geometric patterns for testing software behavior; no patient images or clinical labels.',True,
          {'seed':seed,'count':count,'known_injected_defects':True,'clinical_data':False})
        db.add(d);db.flush()
        dest=DATA_ROOT/d.id/'images';dest.mkdir(parents=True,exist_ok=True)
        samples=[];truth={'label_flip':[],'exact_duplicate':[],'near_duplicate':[],'group_overlap':[],'shortcut_site':{'site_alpha':'pattern_a','site_beta':'pattern_b'}}
        for i in range(count):
            # balanced classes, with site correlated to label but imperfectly
            cls=i%2; true_label=DEMO_LABELS[cls]; site='site_alpha' if (cls==0)==(rng.random()<0.86) else 'site_beta'
            im=Image.new('RGB',(96,96),(23,34,47));draw=ImageDraw.Draw(im)
            noise=rng.normal(0,9,(96,96,3))
            bg=np.clip(np.asarray(im,dtype=np.float32)+noise,0,255).astype('uint8');im=Image.fromarray(bg);draw=ImageDraw.Draw(im)
            cx=48+int(rng.integers(-6,7));cy=49+int(rng.integers(-6,7));r=24+int(rng.integers(-4,5))
            if cls==0: draw.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(143,192,204),width=5)
            else: draw.rectangle((cx-r,cy-r,cx+r,cy+r),outline=(143,192,204),width=5)
            if site=='site_alpha':draw.rectangle((0,0,11,11),fill=(199,133,66))
            else: draw.rectangle((0,0,11,11),fill=(69,150,153))
            split='train' if i%10<7 else ('val' if i%10==7 else 'test')
            gid='phantom-'+str(i//2) if i<8 else 'phantom-'+str(i) # deliberately shared groups for some rows
            label=true_label
            if i in (15,31,47): label=DEMO_LABELS[1-cls];truth['label_flip'].append(f'phantom-{i:04d}')
            filename=f'phantom_{i:04d}.png';im.save(dest/filename)
            s=Sample(dataset_id=d.id,sample_id=f'phantom-{i:04d}',relpath=f'{d.id}/images/{filename}',label=label,split=split,group_id=gid,group_type='synthetic_phantom',site=site,source_id=f'generator-{seed}',sha256=sha_file(dest/filename),width=96,height=96,meta=jd({'synthetic_ground_truth_label':true_label, 'generator_version':'1.0'}))
            samples.append(s)
        # Add one exact byte duplicate across train/test with distinct ID and same phantom group
        original=samples[4];dup_id='phantom-exact-copy';filename='phantom_exact_copy.png';shutil.copy2(safe_path(original.relpath),dest/filename)
        samples.append(Sample(dataset_id=d.id,sample_id=dup_id,relpath=f'{d.id}/images/{filename}',label=original.label,split='test',group_id=original.group_id,group_type='synthetic_phantom',site=original.site,source_id='generated-duplicate',sha256=sha_file(dest/filename),width=96,height=96,meta=jd({'synthetic_defect':'exact_copy','source':original.sample_id})))
        truth['exact_duplicate'].append([original.sample_id,dup_id]);truth['group_overlap'].append(original.group_id)
        # Add near duplicate encoded to separate PNG after slight brightness and compression
        original=samples[8];dup_id='phantom-near-copy';filename='phantom_near_copy.png'
        with Image.open(safe_path(original.relpath)) as im:
            pixels=np.asarray(im).copy();pixels[40:43,40:43]=np.clip(pixels[40:43,40:43].astype(int)+9,0,255).astype('uint8')
            Image.fromarray(pixels).save(dest/filename)
        samples.append(Sample(dataset_id=d.id,sample_id=dup_id,relpath=f'{d.id}/images/{filename}',label=original.label,split='val',group_id=original.group_id,group_type='synthetic_phantom',site=original.site,source_id='generated-near-duplicate',sha256=sha_file(dest/filename),width=96,height=96,meta=jd({'synthetic_defect':'near_copy','source':original.sample_id})))
        truth['near_duplicate'].append([original.sample_id,dup_id]);truth['group_overlap'].append(original.group_id)
        db.add_all(samples);d.manifest_hash=manifest_hash(samples);db.commit()
        (DATA_ROOT/d.id/'synthetic_truth.json').write_text(json.dumps(truth,indent=2),encoding='utf-8')
        return d.id

def _stratified_subset_indices(labels, limit, seed=42):
    """Deterministic class-preserving subset; source indices remain traceable."""
    labels=np.asarray(labels).reshape(-1)
    if len(labels)<=limit:return np.arange(len(labels),dtype=np.int64)
    classes,inverse,counts=np.unique(labels,return_inverse=True,return_counts=True)
    if len(classes)>limit:
        raise ValueError(f'Subset limit {limit} cannot preserve all {len(classes)} classes; increase maximum images per split')
    allocation=np.ones(len(classes),dtype=np.int64)
    capacity=counts-allocation
    remaining=limit-len(classes)
    if remaining:
        fractional=remaining*capacity/capacity.sum()
        allocation+=np.floor(fractional).astype(np.int64)
        extras=limit-int(allocation.sum())
        order=sorted(range(len(classes)),key=lambda j:(-(fractional[j]-np.floor(fractional[j])),-int(capacity[j]),int(j)))
        for j in order:
            if extras==0:break
            if allocation[j]<counts[j]:
                allocation[j]+=1
                extras-=1
    rng=np.random.default_rng(seed)
    selected=np.concatenate([rng.choice(np.flatnonzero(inverse==j),size=int(take),replace=False) for j,take in enumerate(allocation)])
    return np.sort(selected)


def import_npz(path,name,source='MedMNIST',license='Check upstream source dataset license',max_samples_per_split=2000,modality='Other / unspecified'):
    """MedMNIST-compatible arrays only; bounded extraction, no pickle."""
    if max_samples_per_split<10 or max_samples_per_split>10000: raise ValueError('max_samples_per_split must be 10–10000')
    path=Path(path)
    if path.stat().st_size>MAX_NPZ_BYTES:raise ValueError('NPZ upload exceeds 256 MiB safety cap; select a smaller variant')
    with zipfile.ZipFile(path) as container:
        if len(container.infolist())>24 or sum(item.file_size for item in container.infolist())>900*1024*1024:
            raise ValueError('NPZ expanded data exceeds safety limits')
    with np.load(path,allow_pickle=False) as z:
        keys=set(z.files)
        required={'train_images','train_labels','val_images','val_labels','test_images','test_labels'}
        if not required.issubset(keys):raise ValueError('NPZ must contain MedMNIST train/val/test images and labels')
        arrays=[];sizes={};labels_seen=set()
        for split in ['train','val','test']:
            x=z[f'{split}_images'];y=z[f'{split}_labels']
            if len(x)!=len(y) or x.ndim not in (3,4) or x.shape[1]>256 or x.shape[2]>256:
                raise ValueError(f'Unsupported {split} dimensions')
            if x.dtype!=np.uint8 or y.dtype.kind not in ('i','u'):
                raise ValueError('NPZ images must be uint8 and class labels must be integers')
            if y.ndim>2 or (y.ndim==2 and y.shape[1]!=1):raise ValueError('Only single-label classification supported')
            n=min(len(x),max_samples_per_split)
            all_labels=y.reshape(-1)
            indices=_stratified_subset_indices(all_labels,n,seed=42)
            chosen_labels=all_labels[indices].copy()
            arrays.append((split,indices,x[indices].copy(),chosen_labels))
            source_classes,source_counts=np.unique(all_labels,return_counts=True)
            selected_classes,selected_counts=np.unique(chosen_labels,return_counts=True)
            sizes[split]={'source_count':int(len(x)),'imported_count':int(len(indices)),
                          'source_class_counts':{str(int(k)):int(v) for k,v in zip(source_classes,source_counts)},
                          'imported_class_counts':{str(int(k)):int(v) for k,v in zip(selected_classes,selected_counts)},
                          'sampling_policy':'all_images' if len(indices)==len(x) else 'deterministic_class_preserving_seed_42',
                          'evaluation_warning':'Class-preserving subset may not represent source prevalence; never report it as full-dataset evaluation.'}
            labels_seen.update(str(int(t)) for t in chosen_labels)
    with Session() as db:
        d=_dataset(name,source,license,modality,'MedMNIST-compatible NPZ import (bounded, no data downloaded automatically)',False,{'sampling':sizes,'subset':any(v['source_count']!=v['imported_count'] for v in sizes.values()),'label_ids':sorted(labels_seen)})
        db.add(d);db.flush()
        dest=DATA_ROOT/d.id/'images';dest.mkdir(parents=True,exist_ok=True)
        samples=[]
        for split,source_indices,imgs,labels in arrays:
            for source_index,image,label in zip(source_indices,imgs,labels):
                ar=np.asarray(image)
                if ar.ndim==2:im=Image.fromarray(ar.astype('uint8'),'L')
                elif ar.ndim==3 and ar.shape[-1] in (1,3,4):im=Image.fromarray(ar.squeeze(-1).astype('uint8') if ar.shape[-1]==1 else ar.astype('uint8'))
                else:raise ValueError('Unexpected channel shape')
                filename=f'{split}_{int(source_index):05d}.png';im.save(dest/filename)
                p=dest/filename
                samples.append(Sample(dataset_id=d.id,sample_id=f'{split}-{int(source_index):05d}',relpath=f'{d.id}/images/{filename}',
                    label=str(int(label)),split=split,sha256=sha_file(p),width=im.width,height=im.height,
                    meta=jd({'source_index':int(source_index),'sampling_policy':sizes[split]['sampling_policy']})))
        db.add_all(samples);d.manifest_hash=manifest_hash(samples);db.commit()
        return d.id

def import_zip(path,name,source='User-provided image/CSV package',license='Unspecified; verify authorization', modality='Other / unspecified'):
    """ZIP must contain samples.csv and image files; strict traversal/size limits."""
    if modality not in SUPPORTED_MODALITIES: raise ValueError('Unsupported imaging modality declaration')
    path=Path(path)
    if path.stat().st_size>MAX_ARCHIVE_BYTES:raise ValueError('ZIP upload exceeds 150MB limit')
    with zipfile.ZipFile(path) as z:
        infos=z.infolist()
        if len(infos)>12000 or sum(x.file_size for x in infos)>900*1024*1024:raise ValueError('Archive exceeds extraction limits')
        names={x.filename for x in infos}
        if 'samples.csv' not in names:raise ValueError('Archive must contain a root-level samples.csv')
        for info in infos:
            p=Path(info.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in info.filename or (info.external_attr>>16)&0o170000==0o120000:
                raise ValueError('Unsafe archive path/symlink')
        raw=z.read('samples.csv')
        if len(raw)>8*1024*1024:raise ValueError('CSV too large')
        reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
        if not {'sample_id','image_path','label','split'}.issubset(reader.fieldnames or []):raise ValueError('CSV missing required columns')
        rows=list(reader)
        if len(rows)>10000 or len(rows)==0:raise ValueError('CSV must contain 1–10000 rows')
        if len({r['sample_id'] for r in rows})!=len(rows):raise ValueError('Duplicate sample IDs in CSV')
        for r in rows:
            if r['split'] not in ('train','val','test'):raise ValueError('Split must be train, val, or test')
            if r['image_path'] not in names or Path(r['image_path']).suffix.lower() not in ALLOWED_EXT:raise ValueError('Missing or unsupported image: '+r['image_path'][:120])
    with Session() as db:
        d=_dataset(name,source,license,modality,'Imported ZIP+CSV dataset. Image content is kept locally.',False,{'rows':len(rows)})
        db.add(d);db.flush()
        dest=DATA_ROOT/d.id/'images';dest.mkdir(parents=True,exist_ok=True)
        samples=[]
        try:
            with zipfile.ZipFile(path) as z:
                for i,r in enumerate(rows):
                    raw=z.read(r['image_path'])
                    if len(raw)>20*1024*1024:raise ValueError('Image too large')
                    ext=Path(r['image_path']).suffix.lower();filename=f'{i:06d}{ext}';target=dest/filename;target.write_bytes(raw)
                    try:width,height=image_info(target)
                    except ValueError:width=height=None  # detector reports invalid sample
                    samples.append(Sample(dataset_id=d.id,sample_id=r['sample_id'][:200],relpath=f'{d.id}/images/{filename}',label=r['label'][:120],split=r['split'],group_id=(r.get('group_id') or r.get('patient_id') or r.get('lesion_id') or None),group_type=('patient' if r.get('patient_id') else 'lesion' if r.get('lesion_id') else 'unspecified') if (r.get('group_id') or r.get('patient_id') or r.get('lesion_id')) else None,site=r.get('site_id') or None,source_id=r.get('source_record_id') or None,sha256=sha_file(target),width=width,height=height,meta=jd({k:v for k,v in r.items() if k not in ('image_path',)})))
            db.add_all(samples);d.manifest_hash=manifest_hash(samples);db.commit()
            return d.id
        except Exception:
            shutil.rmtree(DATA_ROOT/d.id,ignore_errors=True)
            raise
