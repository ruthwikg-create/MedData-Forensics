"""Controlled lab integrity regressions; synthetic data only."""
import io
import zipfile
import hashlib
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import select
from backend.api import app
from backend.db import Session,Sample,Dataset
from backend.security import safe_path
from backend.worker import run_one


def finish(client,job_id):
    for _ in range(15):
        state=client.get(f'/api/jobs/{job_id}').json()
        if state['status'] in ('completed','failed','cancelled'):
            break
        run_one()
    return client.get(f'/api/jobs/{job_id}').json()


def test_shortcut_only_uses_baseline_leakage_screened_test_split():
    with TestClient(app) as client:
        did=client.post('/api/datasets/demo',json={'count':64,'seed':211}).json()['dataset_id']
        baseline=client.post(f'/api/datasets/{did}/experiments',json={'kind':'baseline','config':{'seed':42}}).json()
        assert finish(client,baseline['job_id'])['status']=='completed'
        summary=client.get(f"/api/experiments/{baseline['experiment_id']}").json()['result']
        probe=client.post(f'/api/datasets/{did}/experiments',json={'kind':'shortcut','config':{}}).json()
        assert finish(client,probe['job_id'])['status']=='completed'
        result=client.get(f"/api/experiments/{probe['experiment_id']}").json()['result']
        assert result['test_n']==min(summary['test_n'],160)
        assert result['evaluation_integrity']['test_retained_n']==summary['evaluation_integrity']['test_retained_n']
        assert result['evaluation_integrity']['excluded_test_n']>=1


def test_cross_dataset_refuses_same_pixels_after_png_reencoding():
    with TestClient(app) as client:
        source_id=client.post('/api/datasets/demo',json={'count':44,'seed':212}).json()['dataset_id']
        baseline=client.post(f'/api/datasets/{source_id}/experiments',json={'kind':'baseline','config':{'seed':42}}).json()
        assert finish(client,baseline['job_id'])['status']=='completed'
        with Session() as db:
            available=db.scalars(select(Sample).where(Sample.dataset_id==source_id)).all()
            originals=[next(x for x in available if x.label==class_name) for class_name in ('pattern_a','pattern_b')]
            inputs=[(x.label,safe_path(x.relpath).read_bytes()) for x in originals]
        archive=io.BytesIO()
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as out:
            entries=['sample_id,image_path,label,split']
            for idx,(label,raw) in enumerate(inputs):
                with Image.open(io.BytesIO(raw)) as img:
                    encoded=io.BytesIO()
                    img.save(encoded,format='PNG',compress_level=0)
                assert hashlib.sha256(encoded.getvalue()).hexdigest()!=hashlib.sha256(raw).hexdigest()
                path=f'images/recoded_{idx}.png'
                out.writestr(path,encoded.getvalue())
                entries.append(f'encoded-{idx},{path},{label},test')
            out.writestr('samples.csv','\n'.join(entries)+'\n')
        archive.seek(0)
        target=client.post('/api/datasets/import',
            data={'name':'Reencoded synthetic external','license':'Synthetic generated test',
                  'source':'Controlled synthetic','modality':'Synthetic geometry (NOT medical images)'},
            files={'file':('encoded.zip',archive,'application/zip')})
        assert target.status_code==200,target.text
        target_id=target.json()['dataset_id']
        external=client.post(f'/api/datasets/{source_id}/experiments',
            json={'kind':'cross_dataset','config':{'target_dataset_id':target_id}}).json()
        failed=finish(client,external['job_id'])
        assert failed['status']=='failed',failed
        assert 'decoded source pixels' in failed['error']


def test_cross_dataset_readiness_explains_missing_or_incompatible_target_and_blocks_launch():
    with TestClient(app) as client:
        source_id=client.post('/api/datasets/demo',json={'count':48,'seed':231}).json()['dataset_id']
        target_id=client.post('/api/datasets/demo',json={'count':48,'seed':232}).json()['dataset_id']
        empty=client.get(f'/api/datasets/{source_id}/cross-dataset-readiness').json()
        target_summary=next(item for item in empty['targets'] if item['id']==target_id)
        assert target_summary['compatible'] is True
        assert empty['baseline_ready'] is False

        baseline=client.post(f'/api/datasets/{source_id}/experiments',
            json={'kind':'baseline','config':{'seed':42}}).json()
        assert finish(client,baseline['job_id'])['status']=='completed'
        ready=client.get(f'/api/datasets/{source_id}/cross-dataset-readiness').json()
        assert ready['baseline_ready'] is True
        assert next(item for item in ready['targets'] if item['id']==target_id)['compatible'] is True

        with Session() as db:
            db.get(Dataset,target_id).modality='Histopathology'
            db.commit()
        incompatible=client.get(f'/api/datasets/{source_id}/cross-dataset-readiness').json()
        target=next(item for item in incompatible['targets'] if item['id']==target_id)
        assert target['compatible'] is False
        assert any('modality' in reason.lower() for reason in target['reasons'])
        blocked=client.post(f'/api/datasets/{source_id}/experiments',
            json={'kind':'cross_dataset','config':{'target_dataset_id':target_id}})
        assert blocked.status_code==422
        assert 'modality' in blocked.json()['detail'].lower()


def test_impact_readiness_blocks_empty_run_then_allows_confirmed_train_evidence():
    with TestClient(app) as client:
        did=client.post('/api/datasets/demo',json={'count':64,'seed':42}).json()['dataset_id']
        initial=client.get(f'/api/datasets/{did}/impact-readiness').json()
        assert initial['ready'] is False
        assert initial['audit_completed'] is False
        assert any('Forensic Audit' in reason for reason in initial['reasons'])
        blocked=client.post(f'/api/datasets/{did}/experiments',
            json={'kind':'impact','config':{'seed':42}})
        assert blocked.status_code==422
        assert 'Impact Simulator cannot start' in blocked.json()['detail']

        audit=client.post(f'/api/datasets/{did}/audit').json()
        assert finish(client,audit['job_id'])['status']=='completed'
        findings=client.get(f'/api/datasets/{did}/findings?size=200').json()['items']
        train_ids={item['id'] for item in client.get(
            f'/api/datasets/{did}/samples?split=train&size=100').json()['items']}
        supported={'split_leakage','group_overlap','exact_duplicate','pixel_duplicate','near_duplicate','label_suspicion'}
        finding=next(item for item in findings if item['kind'] in supported and
            any(sid in train_ids for sid in (item['sample_id'],item['linked_id']) if sid))
        review=client.post(f"/api/findings/{finding['id']}/review",
            json={'reviewer':'QA researcher','decision':'confirmed',
                  'notes':'Confirmed after inspecting the linked training image evidence.'})
        assert review.status_code==200

        ready=client.get(f'/api/datasets/{did}/impact-readiness').json()
        assert ready['ready'] is True,ready
        assert ready['confirmed_training_samples']>=1
        assert ready['confirmed_exclusions_in_model_fit']>=1
        experiment=client.post(f'/api/datasets/{did}/experiments',
            json={'kind':'impact','config':{'seed':42}})
        assert experiment.status_code==200,experiment.text
        result=finish(client,experiment.json()['job_id'])
        assert result['status']=='completed',result
        output=client.get('/api/experiments/'+experiment.json()['experiment_id']).json()['result']
        assert output['removed_count']>=1
        assert output['evaluation_test_ids_sha256']
