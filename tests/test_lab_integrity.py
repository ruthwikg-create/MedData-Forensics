"""Controlled lab integrity regressions; synthetic data only."""
import io
import zipfile
import hashlib
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import select
from backend.api import app
from backend.db import Session,Sample
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
