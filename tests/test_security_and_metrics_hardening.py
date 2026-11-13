"""Regression tests for hardened local sessions, immutable hashes and evaluation integrity."""
from types import SimpleNamespace
import io
import zipfile

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.api import app
from backend.labs import _evaluation_integrity, _score


def _sample(name, split, pixel, group=None, sha=None):
    return SimpleNamespace(id=name, sample_id=name, label='a', split=split,
                           group_id=group, group_type='patient',
                           sha256=sha or name, pixelhash=pixel)


def test_local_access_gate_blocks_remote_peer_and_wildcard_binding(monkeypatch):
    monkeypatch.delenv('MDF_ACCESS_TOKEN', raising=False)
    monkeypatch.setenv('MDF_HOST','0.0.0.0')
    with TestClient(app) as client:
        assert client.get('/api/overview').status_code==401
        assert client.post('/api/session').status_code==401
    monkeypatch.setenv('MDF_HOST','127.0.0.1')
    with TestClient(app,client=('203.0.113.20',50001)) as client:
        assert client.get('/api/overview').status_code==401
    with TestClient(app,client=('127.0.0.1',50001)) as client:
        assert client.get('/api/overview').status_code==200


def test_cookie_is_not_shared_master_token_and_logout_revokes(monkeypatch):
    token='test-workstation-secret-long-and-random'
    monkeypatch.setenv('MDF_ACCESS_TOKEN',token)
    monkeypatch.setenv('MDF_HOST','127.0.0.1')
    with TestClient(app) as client:
        assert client.get('/api/overview').status_code==401
        client.cookies.set('mdf_access',token)
        assert client.get('/api/overview').status_code==401
        client.cookies.clear()
        assert client.post('/api/session',headers={'X-MDF-Token':'wrong'}).status_code==401
        response=client.post('/api/session',headers={'X-MDF-Token':token})
        assert response.status_code==200
        cookie=client.cookies.get('mdf_access')
        assert cookie and cookie!=token
        assert token not in response.headers['set-cookie']
        assert 'httponly' in response.headers['set-cookie'].lower()
        assert 'samesite=strict' in response.headers['set-cookie'].lower()
        assert client.get('/api/overview').status_code==200
        assert client.post('/api/session').status_code==401
        assert client.post('/api/logout').status_code==200
        client.cookies.set('mdf_access',cookie)
        assert client.get('/api/overview').status_code==401


def test_HTTPS_marks_cookie_secure(monkeypatch):
    token='test-other-workstation-long-secret'
    monkeypatch.setenv('MDF_ACCESS_TOKEN',token)
    with TestClient(app,base_url='https://localhost') as client:
        response=client.post('/api/session',headers={'X-MDF-Token':token})
        assert response.status_code==200
        assert 'secure' in response.headers['set-cookie'].lower()


def test_transitive_train_validation_test_links_are_not_evaluated():
    train=[_sample('train','train','px1',group='patient-A')]
    val=[_sample('validation','val','px2',group='patient-A')]
    test=[_sample('leaking-test','test','px2'),_sample('safe-test','test','px3')]
    valid,held,details=_evaluation_integrity(train,val,test)
    assert valid==[]
    assert [s.id for s in held]==['safe-test']
    assert details['excluded_test_n']==1


def test_duplicate_test_images_count_once():
    train=[_sample('training','train','trainpixel')]
    test=[_sample('a','test','identical'),_sample('b','test','identical'),
          _sample('c','test','independent')]
    _,held,details=_evaluation_integrity(train,[],test)
    assert [s.id for s in held]==['a','c']
    assert details['duplicate_test_n']==1


def test_exact_metric_reference_values(monkeypatch):
    import backend.labs as labs
    rows=[SimpleNamespace(label=y, sample_id=f'test-{i}',id=f'id-{i}',
          split='test',site='synthetic',group_id=None,group_type=None,
          sha256=f'hash-{i}') for i,y in enumerate(['a','a','b','b'])]
    model=SimpleNamespace(classes_=np.array(['a','b']))
    monkeypatch.setattr(labs,'_pred',lambda model,rows:
        np.array([[.9,.1],[.4,.6],[.2,.8],[.1,.9]]))
    metrics=_score(model,rows)['metrics']
    assert metrics['confusion_matrix']==[[1,1],[0,2]]
    assert metrics['accuracy']==pytest.approx(.75)
    assert metrics['macro_f1']==pytest.approx(((2/3)+(4/5))/2)
    assert metrics['brier_multiclass']==pytest.approx((.02+.72+.08+.02)/4)


def test_audit_preserves_original_hash_when_local_file_changes(monkeypatch):
    from backend.db import Session,Sample
    from backend.security import safe_path
    from backend.worker import run_one
    monkeypatch.delenv('MDF_ACCESS_TOKEN',raising=False)
    monkeypatch.setenv('MDF_HOST','127.0.0.1')
    monkeypatch.setenv('MDF_NO_AUTOWORKER','1')
    with TestClient(app) as client:
        did=client.post('/api/datasets/demo',json={'seed':54321,'count':40}).json()['dataset_id']
        with Session() as db:
            s=db.query(Sample).filter(Sample.dataset_id==did).first()
            old_hash=s.sha256
            path=safe_path(s.relpath)
        original=path.read_bytes()
        try:
            path.write_bytes(original+b'file-has-changed')
            job=client.post(f'/api/datasets/{did}/audit').json()
            assert run_one()
            assert client.get('/api/jobs/'+job['job_id']).json()['status']=='completed'
            with Session() as db:
                assert db.get(Sample,s.id).sha256==old_hash
            result=client.get(f'/api/datasets/{did}/verify').json()
            assert any(x.get('kind')=='changed_file_hash' for x in result['problems'])
        finally:
            path.write_bytes(original)


def test_zip_oversize_csv_is_rejected_before_decompression(tmp_path):
    from backend.ingest import import_zip
    archive=tmp_path/'oversized.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('samples.csv','sample_id,image_path,label,split\\n'+'x'*(8*1024*1024))
    with pytest.raises(ValueError,match='CSV too large'):
        import_zip(archive,'test')
