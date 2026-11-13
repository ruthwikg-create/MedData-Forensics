"""Strict software release-gate regression tests; all images are synthetic."""
import io
import json
import os
import zipfile
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from backend.api import app
from backend.db import Session,Sample
from backend.security import safe_path
from backend.worker import run_one
from backend.labs import _evaluation_integrity


def _job(client,jid):
    for i in range(5):
        state=client.get('/api/jobs/'+jid).json()
        if state['status'] in ('completed','failed','cancelled'):
            break
        assert run_one()
    final=client.get('/api/jobs/'+jid).json()
    assert final['status']=='completed',final


def test_real_integrity_check_detects_modified_files_and_export_contains_verification():
    with TestClient(app) as client:
        did=client.post('/api/datasets/demo',json={'seed':191,'count':40}).json()['dataset_id']
        pristine=client.get(f'/api/datasets/{did}/verify').json()
        assert pristine['passed'] is True
        with Session() as db:
            one=db.query(Sample).filter(Sample.dataset_id==did).first()
            path=safe_path(one.relpath)
        before=path.read_bytes()
        try:
            path.write_bytes(before+b'attack')
            invalid=client.get(f'/api/datasets/{did}/verify').json()
            assert not invalid['passed']
            assert 'changed_file_hash' in {x['kind'] for x in invalid['problems']}
        finally:
            path.write_bytes(before)
        assert client.get(f'/api/datasets/{did}/verify').json()['passed']
        report=client.get(f'/api/datasets/{did}/report?format=repro')
        assert report.status_code==200
        content=report.json()['reproducibility_bundle']
        assert content['verification']['passed']
        assert len(content['sample_manifest'])==42
        assert content['export_omits_images_and_model_binaries']


def test_reviews_are_reversible_with_history_and_traceable_evidence():
    with TestClient(app) as client:
        did=client.post('/api/datasets/demo',json={'seed':188,'count':40}).json()['dataset_id']
        job=client.post(f'/api/datasets/{did}/audit').json()
        _job(client,job['job_id'])
        first=client.get(f'/api/datasets/{did}/findings').json()['items'][0]
        evidence=client.get('/api/findings/'+first['id']).json()['finding']['evidence']
        assert evidence['detector_version'] and evidence['limitation']
        for decision in ('confirmed','rejected','uncertain'):
            reply=client.post(f"/api/findings/{first['id']}/review",json={
                'decision':decision,'reviewer':'Test QA','notes':'Controlled review revision'})
            assert reply.status_code==200
        r=client.get('/api/findings/'+first['id']).json()
        assert r['finding']['status']=='uncertain'
        assert len(r['reviews'])==3
        assert {x['decision'] for x in r['reviews']}=={'confirmed','rejected','uncertain'}
        assert r['finding']['audit_id']


def test_leakage_guard_excludes_known_provenance_overlaps_and_cluster_intervals():
    with TestClient(app) as client:
        did=client.post('/api/datasets/demo',json={'seed':177,'count':64}).json()['dataset_id']
        with Session() as db:
            all_samples=db.query(Sample).filter(Sample.dataset_id==did).all()
            train=[x for x in all_samples if x.split=='train']
            val=[x for x in all_samples if x.split=='val']
            test=[x for x in all_samples if x.split=='test']
            screened_val,screened_test,meta=_evaluation_integrity(train,val,test)
            assert meta['excluded_test_n']>=1
            assert len(screened_test)<len(test)
        e=client.post(f'/api/datasets/{did}/experiments',json={'kind':'baseline','config':{'seed':42}}).json()
        _job(client,e['job_id'])
        result=client.get('/api/experiments/'+e['experiment_id']).json()['result']
        assert result['evaluation_integrity']['excluded_test_n']>=1
        assert result['test_n']==len(screened_test)
        metrics=result['test']['metrics']
        assert metrics['bootstrap_method'].startswith('group-cluster')
        assert metrics['bootstrap_resamples']==300
        assert 0<=metrics['macro_f1_ci95'][0]<=metrics['macro_f1_ci95'][1]<=1
        assert metrics['bootstrap_clusters']<=metrics['n']


def test_igat_synthetic_comparison_is_fair_and_real_unverified_not_scored():
    with TestClient(app) as client:
        did=client.post('/api/datasets/demo',json={'seed':178,'count':40}).json()['dataset_id']
        job=client.post(f'/api/datasets/{did}/audit').json()
        _job(client,job['job_id'])
        r=client.get(f'/api/datasets/{did}/rankings?budget=5').json()
        assert r['ground_truth_available']
        assert len(r['strategies'])==4
        assert all(x['review_budget']==5 for x in r['strategies'])
        random_strategy=next(x for x in r['strategies'] if x['name'].startswith('Random'))
        assert len(random_strategy['trial_seeds'])==30
        assert len(random_strategy['trial_yield_95pct_interval'])==2


def test_local_token_protects_data_routes_when_enabled(monkeypatch):
    monkeypatch.setenv('MDF_ACCESS_TOKEN','temporary-test-token')
    with TestClient(app) as client:
        assert client.get('/api/overview').status_code==401
        assert client.post('/api/session',headers={'X-MDF-Token':'wrong'}).status_code==401
        assert client.post('/api/session',headers={'X-MDF-Token':'temporary-test-token'}).status_code==200
        assert client.get('/api/overview').status_code==200


def test_unsafe_zip_path_is_rejected():
    with TestClient(app) as client:
        bio=io.BytesIO()
        with zipfile.ZipFile(bio,'w') as z:
            z.writestr('samples.csv','sample_id,image_path,label,split\none,../bad.png,0,train\n')
            z.writestr('../bad.png',b'unsafe')
        bio.seek(0)
        r=client.post('/api/datasets/import',data={'name':'Unsafe ZIP'},files={'file':('bad.zip',bio,'application/zip')})
        assert r.status_code==422


def test_network_binding_without_secret_is_rejected(monkeypatch):
    monkeypatch.delenv('MDF_ACCESS_TOKEN', raising=False)
    monkeypatch.setenv('MDF_HOST', '0.0.0.0')
    with TestClient(app) as client:
        assert client.get('/api/overview').status_code == 401
        assert client.post('/api/session').status_code == 401


def test_loopback_without_secret_stays_usable(monkeypatch):
    monkeypatch.delenv('MDF_ACCESS_TOKEN', raising=False)
    monkeypatch.setenv('MDF_HOST', '127.0.0.1')
    with TestClient(app) as client:
        assert client.get('/api/overview').status_code == 200
