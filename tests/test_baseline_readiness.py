"""Regression tests for actionable baseline prerequisites and deterministic CPU training."""
from types import SimpleNamespace

import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.api import app
from backend.db import Session, Sample
from backend import labs


def test_sandbox_baseline_readiness_and_unavailable_model():
    with TestClient(app) as client:
        did=client.post('/api/datasets/demo',json={'count':64,'seed':321}).json()['dataset_id']
        response=client.get(f'/api/datasets/{did}/baseline-readiness')
        assert response.status_code==200
        ready=response.json()
        assert ready['ready'] is True,ready
        assert ready['split_counts']['train']>=20
        assert ready['split_counts']['test']>0
        assert ready['errors']==[]
        assert client.get(f'/api/jobs?dataset_id={did}').status_code==200
        # No completed baseline exists, so dependent labs cannot be queued.
        response=client.post(f'/api/datasets/{did}/experiments',json={'kind':'shortcut'})
        assert response.status_code==422
        assert 'baseline' in response.json()['detail'].lower()


def test_baseline_preflight_blocks_missing_test_split():
    with TestClient(app) as client:
        did=client.post('/api/datasets/demo',json={'count':64,'seed':322}).json()['dataset_id']
        with Session() as db:
            for sample in db.scalars(select(Sample).where(Sample.dataset_id==did,Sample.split=='test')):
                sample.split='val'
            db.commit()
        result=client.get(f'/api/datasets/{did}/baseline-readiness').json()
        assert result['ready'] is False
        assert 'test split' in ' '.join(result['errors']).lower()
        response=client.post(f'/api/datasets/{did}/experiments',json={'kind':'baseline'})
        assert response.status_code==422
        assert 'test split' in response.json()['detail'].lower()


def test_baseline_preflight_blocks_test_group_overlap():
    with TestClient(app) as client:
        did=client.post('/api/datasets/demo',json={'count':64,'seed':323}).json()['dataset_id']
        with Session() as db:
            train=db.scalars(select(Sample).where(Sample.dataset_id==did,Sample.split=='train')).first()
            assert train
            for sample in db.scalars(select(Sample).where(Sample.dataset_id==did,Sample.split=='test')):
                sample.group_id=train.group_id
                sample.group_type=train.group_type
            db.commit()
        result=client.get(f'/api/datasets/{did}/baseline-readiness').json()
        assert result['ready'] is False,result
        assert 'independent' in ' '.join(result['errors']).lower()
        assert result['overlap_test_records']==result['split_counts']['test']


def test_capped_training_keeps_minority_class(monkeypatch):
    # Ordered-by-label data previously lost the minority class after [:max_train].
    rows=[SimpleNamespace(id=str(i),label='a' if i<36 else 'b',relpath=f'fake/{i}.png') for i in range(42)]
    def fake_extract(path):
        i=int(path.stem)
        return np.asarray([float(i%3),float(i>=36),float(i%5)],dtype=np.float64)
    monkeypatch.setattr(labs,'extract_features',fake_extract)
    model=labs._model(rows,seed=42,max_train=20)
    assert set(model.classes_)=={'a','b'}
