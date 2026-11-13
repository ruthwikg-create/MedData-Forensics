"""Regressions for sorted imports, imbalanced baseline models, and actionable failures.

All images are newly generated synthetic noise. No medical validity is asserted.
"""
import io
import numpy as np
from fastapi.testclient import TestClient
from backend.api import app
from backend.db import Session,Dataset,Sample,Experiment,Job,ARTIFACT_ROOT
from backend.ingest import _stratified_subset_indices
from backend.worker import run_one


def test_class_preserving_subset_is_reproducible_and_traceable():
    labels=np.asarray([0]*90+[1]*8+[2]*2)
    indices=_stratified_subset_indices(labels,25,seed=42)
    assert len(indices)==25
    assert len(set(indices.tolist()))==25
    assert np.all(np.diff(indices)>0)
    assert set(labels[indices])=={0,1,2}
    assert np.array_equal(indices,_stratified_subset_indices(labels,25,seed=42))


def test_import_sorted_rare_class_trains_with_explicit_warnings():
    rng=np.random.default_rng(2026)
    labels={
        'train':np.asarray([0]*79+[1],dtype=np.uint8),
        'val':np.asarray([0]*17+[1],dtype=np.uint8),
        'test':np.asarray([0]*17+[1],dtype=np.uint8),
    }
    arrays={}
    for split,y in labels.items():
        arrays[split+'_images']=rng.integers(0,255,size=(len(y),28,28,3),dtype=np.uint8)
        arrays[split+'_labels']=y.reshape(-1,1)
    buf=io.BytesIO()
    np.savez_compressed(buf,**arrays)
    buf.seek(0)
    with TestClient(app) as client:
        response=client.post('/api/datasets/import',
            data={'name':'Sorted class-preservation experiment','source':'Local generated noise',
                  'license':'Synthetic generated regression','max_per_split':'30'},
            files={'file':('synthetic.npz',buf,'application/octet-stream')})
        assert response.status_code==200,response.text
        did=response.json()['dataset_id']
        detail=client.get(f'/api/datasets/{did}').json()
        sampled=detail['dataset']['metadata']['sampling']
        assert sampled['train']['source_count']==80
        assert sampled['train']['imported_count']==30
        assert sampled['train']['sampling_policy']=='deterministic_class_preserving_seed_42'
        assert sampled['train']['imported_class_counts']['1']==1
        with Session() as db:
            rows=db.query(Sample).filter(Sample.dataset_id==did,Sample.split=='train').all()
            assert len(rows)==30
            minority=[x for x in rows if x.label=='1']
            assert len(minority)==1
            assert minority[0].sample_id=='train-00079'
            assert minority[0].metadata is not None if hasattr(minority[0],'metadata') else True
        readiness=client.get(f'/api/datasets/{did}/baseline-readiness')
        assert readiness.status_code==200,readiness.text
        check=readiness.json()
        assert check['ready'],check
        assert check['training_class_counts']['1']==1
        assert any('fewer than 3' in msg for msg in check['warnings'])
        job=client.post(f'/api/datasets/{did}/experiments',
            json={'kind':'baseline','config':{'seed':42}})
        assert job.status_code==200,job.text
        job_id=job.json()['job_id']
        for _ in range(30):
            state=client.get(f'/api/jobs/{job_id}').json()
            if state['status'] in ('completed','failed','cancelled'):break
            run_one()
        final=client.get(f'/api/jobs/{job_id}').json()
        assert final['status']=='completed',final
        out=client.get(f"/api/experiments/{job.json()['experiment_id']}").json()
        assert out['checkpoint_available']
        assert out['result']['training_class_counts']['1']==1
        assert out['result']['training_warnings']
        assert out['result']['test']['metrics']['n']>0


def test_baseline_preflight_rejects_invalid_training_data_before_queuing():
    with TestClient(app) as client:
        one=client.post('/api/datasets/demo',json={'seed':54,'count':40}).json()['dataset_id']
        with Session() as db:
            rows=db.query(Sample).filter(Sample.dataset_id==one,Sample.split=='train').all()
            for row in rows:row.label='one_class'
            db.commit()
        status=client.get(f'/api/datasets/{one}/baseline-readiness').json()
        assert not status['ready']
        assert any('2 training classes' in v for v in status['reasons'])
        refused=client.post(f'/api/datasets/{one}/experiments',
            json={'kind':'baseline','config':{}})
        assert refused.status_code==422
        assert '2 training classes' in refused.text
        blocked=client.post(f'/api/datasets/{one}/experiments',
            json={'kind':'shortcut','config':{}})
        assert blocked.status_code==422
        assert 'saved model file' in blocked.text


def test_completed_baseline_status_without_checkpoint_does_not_unlock_labs():
    with TestClient(app) as client:
        did=client.post('/api/datasets/demo',json={'seed':94,'count':40}).json()['dataset_id']
        with Session() as db:
            phantom=Experiment(dataset_id=did,kind='baseline',status='completed',config='{}',result='{}')
            db.add(phantom)
            db.commit()
            eid=phantom.id
        assert not (ARTIFACT_ROOT/eid/'baseline.joblib').exists()
        detail=client.get(f'/api/datasets/{did}').json()
        done=next(e for e in detail['experiments'] if e['id']==eid)
        assert done['status']=='completed'
        assert done['checkpoint_available'] is False
        refused=client.post(f'/api/datasets/{did}/experiments',json={'kind':'counterfactual','config':{'sample_id':'sample'}})
        assert refused.status_code==422
