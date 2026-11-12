import io,csv,zipfile,os,json
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import select
from backend.api import app
from backend.db import Session,Job,Dataset,Sample,Finding,Experiment
from backend.worker import run_one
from backend.security import safe_path

@pytest.fixture(scope='module')
def client():
    with TestClient(app) as c:yield c

@pytest.fixture(scope='module')
def sandbox(client):
    r=client.post('/api/datasets/demo',json={'count':64,'seed':42});assert r.status_code==200,r.text
    return r.json()['dataset_id']

def run_job(client,jid):
    for _ in range(5):
        status=client.get('/api/jobs/'+jid).json()
        if status['status'] in ('completed','failed','cancelled'):break
        assert run_one()
    state=client.get('/api/jobs/'+jid).json()
    assert state['status']=='completed',state
    return state

def test_health_overview_and_dna(client,sandbox):
    assert client.get('/api/health').status_code==200
    home=client.get('/');assert home.status_code==200 and b'MedData' in home.content
    assert client.get('/assets/app.js').status_code==200
    o=client.get('/api/overview').json();assert o['datasets']>=1
    dna=client.get(f'/api/datasets/{sandbox}/dna').json()
    assert dna['dataset']['synthetic'] and dna['group_coverage']['with_group_id']>0
    assert dna['splits']['test']>0 and dna['labels']['pattern_a']>0
    samples=client.get(f'/api/datasets/{sandbox}/samples').json();assert samples['count']==66
    assert client.get(samples['items'][0]['image_url']).headers['content-type'].startswith('image/')

def test_audit_and_review(client,sandbox):
    r=client.post(f'/api/datasets/{sandbox}/audit');assert r.status_code==200
    run_job(client,r.json()['job_id'])
    results=client.get(f'/api/datasets/{sandbox}/findings').json();assert results['count']>3
    kinds={f['kind'] for f in results['items']}
    assert 'split_leakage' in kinds and 'group_overlap' in kinds and 'label_suspicion' in kinds
    finding=next(f for f in results['items'] if f['kind']=='split_leakage')
    x=client.get('/api/findings/'+finding['id']).json();assert x['sample'] and x['linked']
    response=client.post('/api/findings/'+finding['id']+'/review',json={'reviewer':'QA researcher','decision':'confirmed','notes':'The two image files have the same image-content hash.','duration_seconds':23})
    assert response.status_code==200
    record=client.get('/api/findings/'+finding['id']).json()
    assert record['finding']['status']=='confirmed' and len(record['reviews'])==1
    assert client.get(f'/api/datasets/{sandbox}/graph').json()['nodes']
    rankings=client.get(f'/api/datasets/{sandbox}/rankings').json()
    assert rankings['ground_truth_available'] and len(rankings['strategies'])==4

def test_baseline_and_all_labs(client,sandbox):
    def experiment(kind,config={}):
        r=client.post(f'/api/datasets/{sandbox}/experiments',json={'kind':kind,'config':config})
        assert r.status_code==200,r.text
        run_job(client,r.json()['job_id'])
        return client.get('/api/experiments/'+r.json()['experiment_id']).json()
    baseline=experiment('baseline',{'seed':42})
    assert baseline['result']['test']['metrics']['n']>=10
    assert baseline['result']['manifest']['research_only']
    assert baseline['result']['test']['metrics']['macro_f1_ci95']
    shortcut=experiment('shortcut')
    assert 0<=shortcut['result']['prediction_flip_rate']<=1
    ids=client.get(f'/api/datasets/{sandbox}/samples').json()['items']
    cf=experiment('counterfactual',{'sample_id':ids[0]['id']})
    assert len(cf['result']['variants'])==4
    assert client.get('/artifacts/'+cf['result']['variants'][0]['image_path']).status_code==200
    impact=experiment('impact')
    assert impact['result']['removed_count']>=1
    assert impact['result']['evaluation_test_ids_sha256']
    scenario=experiment('scenario',{'seed':91,'label_flip_rate':.09})
    derived=scenario['result']['derived_dataset_id']
    v=client.get('/api/datasets/'+derived).json()
    assert v['dataset']['parent_id']==sandbox and v['dataset']['sample_count']==66
    src=client.get(f'/api/datasets/{sandbox}').json()['dataset']
    assert v['dataset']['manifest_hash']!=src['manifest_hash']
    for fmt in ['json','csv','html']:
        r=client.get(f'/api/datasets/{sandbox}/report?format={fmt}')
        assert r.status_code==200 and 'attachment' in r.headers['content-disposition']
    assert client.get('/artifacts/'+scenario['result']['truth_artifact']).status_code==200
    return derived

def test_cross_dataset(client,sandbox):
    source=client.post(f'/api/datasets/{sandbox}/experiments',json={'kind':'baseline','config':{}}).json()
    run_job(client,source['job_id'])
    target=client.post('/api/datasets/demo',json={'seed':77,'count':64}).json()['dataset_id']
    resp=client.post(f'/api/datasets/{sandbox}/experiments',json={'kind':'cross_dataset','config':{'target_dataset_id':target}}).json()
    run_job(client,resp['job_id'])
    output=client.get('/api/experiments/'+resp['experiment_id']).json()
    assert output['result']['external_test']['metrics']['n']>0

def test_npz_and_zip_import(client):
    images=np.zeros((8,28,28,3),dtype='uint8');labels=np.array([[0],[1],[0],[1],[0],[1],[0],[1]])
    bio=io.BytesIO();np.savez_compressed(bio,train_images=images,train_labels=labels,val_images=images[:4],val_labels=labels[:4],test_images=images[:4],test_labels=labels[:4]);bio.seek(0)
    r=client.post('/api/datasets/import',data={'name':'Small NPZ','source':'Generated test','license':'Test only','max_per_split':'20'},files={'file':('test.npz',bio,'application/octet-stream')})
    assert r.status_code==200,r.text
    assert client.get('/api/datasets/'+r.json()['dataset_id']).json()['dataset']['sample_count']==16
    bio=io.BytesIO()
    with zipfile.ZipFile(bio,'w') as z:
        pic=io.BytesIO();Image.new('RGB',(28,28),'blue').save(pic,format='PNG');z.writestr('images/one.png',pic.getvalue())
        z.writestr('samples.csv','sample_id,image_path,label,split,patient_id,site_id\none,images/one.png,healthy,train,p001,alpha\n')
    bio.seek(0)
    r=client.post('/api/datasets/import',data={'name':'Small ZIP','source':'Generated','license':'CC0'},files={'file':('test.zip',bio,'application/zip')})
    assert r.status_code==200,r.text
    detail=client.get('/api/datasets/'+r.json()['dataset_id']).json()
    assert detail['groups_with_ids']==1

def test_security_restrictions(client):
    assert client.post('/api/datasets/import',data={'name':'Unsafe'},files={'file':('test.txt',b'abcd','text/plain')}).status_code==415
    with pytest.raises(ValueError):safe_path('../../etc/passwd')
    assert client.get('/artifacts/../../etc/passwd').status_code in (404,401)
    assert client.get('/api/privacy').json()['telemetry'] is False
    assert client.get('/api/session').status_code==405
