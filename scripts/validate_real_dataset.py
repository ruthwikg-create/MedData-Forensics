"""Licensed-dataset smoke evaluation. Never invents clinical metrics.

Example (Windows, in project root):
  .venv\\Scripts\\python.exe scripts\\validate_real_dataset.py --download-pneumoniamnist

The official source is Zenodo MedMNIST (CC BY 4.0). Internet needed once.
This exercise does not count as independent patient/clinical validation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

URL='https://zenodo.org/records/10519652/files/pneumoniamnist.npz?download=1'
EXPECTED_MD5='28209eda62fecd6e6a2d98b1501bb15f'


def digest(path,kind='md5'):
    h=hashlib.new(kind)
    with Path(path).open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description='Real MedMNIST licensed source smoke test; research only')
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--download-pneumoniamnist',action='store_true',help='download official CC BY 4.0 source from Zenodo')
    group.add_argument('--file',type=Path,help='previously downloaded MedMNIST-compatible NPZ')
    parser.add_argument('--max-per-split',type=int,default=600,help='CPU-friendly source cap per train/val/test split (default 600)')
    parser.add_argument('--md5',help='expected MD5 for custom file; default official PneumoniaMNIST hash')
    args=parser.parse_args()
    if args.max_per_split<40 or args.max_per_split>2000:parser.error('max-per-split must be between 40 and 2000')
    target=args.file
    dataset_name='User-provided MedMNIST-compatible data'
    license_note='User must independently verify the source license and authorized use'
    source='User-provided research dataset'
    if args.download_pneumoniamnist:
        target=ROOT/'data'/'official_downloads'/'pneumoniamnist.npz'
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists() or digest(target)!=EXPECTED_MD5:
            print('Downloading only the official Zenodo PneumoniaMNIST data; no clinical use.')
            urllib.request.urlretrieve(URL,target)
        dataset_name='PneumoniaMNIST (official, CC BY 4.0)'
        license_note='CC BY 4.0 — cite MedMNIST and original PneumoniaMNIST source publication; research only'
        source=URL
    if not target or not target.is_file():raise SystemExit('Dataset file does not exist')
    expected=args.md5 or (EXPECTED_MD5 if args.download_pneumoniamnist else None)
    if expected and digest(target)!=expected:
        raise SystemExit('Dataset checksum failed. Do not use this file.')
    from backend.db import Session,AuditRun,Experiment,jd,ARTIFACT_ROOT
    from backend.ingest import import_npz
    from backend.analysis_engine import audit,ranking_comparison
    from backend.labs import run_baseline
    from backend.api import verify_dataset_integrity
    print('Importing into the local research DB; original NPZ is not changed.')
    did=import_npz(target,dataset_name,source,license_note,args.max_per_split)
    with Session() as db:
        a=AuditRun(dataset_id=did,status='queued',config=jd({'purpose':'licensed dataset smoke test'}))
        db.add(a);db.commit();aid=a.id
    summary=audit(did,aid)
    with Session() as db:
        e=Experiment(dataset_id=did,kind='baseline',status='queued',config=jd({'seed':42,'purpose':'licensed dataset smoke test'}))
        db.add(e);db.commit();eid=e.id
    result=run_baseline(eid)
    integrity=verify_dataset_integrity(did)
    report={'dataset_id':did,'source':source,'source_md5':digest(target),
            'license_claim_from_official_source':license_note,'research_only':True,
            'audit_summary':summary,'evaluation_integrity':result['evaluation_integrity'],
            'test_metrics':result['test']['metrics'], 'integrity_verification':integrity,
            'limitations':['This is a software smoke test on published benchmark data, not independent clinical validation.',
                           'Images are 28x28 standardized research samples, with no guaranteed patient identities.',
                           'Source splits and any imported subsets require dataset-specific review before publication.',
                           'This script does not supply expert review or a complete IGAT-vs-Cleanlab study.']}
    dest=ARTIFACT_ROOT/f'licensed_dataset_smoke_{did}.json'
    dest.write_text(json.dumps(report,indent=2,default=str),encoding='utf-8')
    print(f"Dataset ID: {did}; image integrity: {'PASS' if integrity['passed'] else 'FAIL'}")
    print('Macro-F1 on screened test partition:',result['test']['metrics']['macro_f1'])
    print('Written:',dest)
    if not integrity['passed']:raise SystemExit('Integrity verification FAILED')

if __name__=='__main__':main()
