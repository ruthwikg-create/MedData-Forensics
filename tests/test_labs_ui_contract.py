"""Regressions for UI-visible research results and honest evaluation prerequisites."""
from fastapi.testclient import TestClient
from sqlalchemy import select
from backend.api import app
from backend.db import Session,Dataset
from backend.worker import run_one

def run_job(client,job_id):
    for _ in range(10):
        job=client.get('/api/jobs/'+job_id).json()
        if job['status'] in ('completed','failed','cancelled'):break
        assert run_one()
    assert job['status']=='completed',job

def test_graph_ranking_and_strength_visible_on_synthetic_workflow():
    with TestClient(app) as c:
        did=c.post('/api/datasets/demo',json={'seed':53,'count':64}).json()['dataset_id']
        preview=c.get(f'/api/datasets/{did}/graph').json()
        assert preview['network_mode']=='sample_inventory'
        assert preview['audit_completed'] is False
        assert preview['edges']==[]
        assert 0<len(preview['nodes'])<=12
        r=c.post(f'/api/datasets/{did}/audit').json();run_job(c,r['job_id'])
        graph=c.get(f'/api/datasets/{did}/graph').json()
        assert graph['audit_completed'] is True
        assert graph['network_mode']=='evidence'
        assert len(graph['edges'])>=1
        scored=c.get(f'/api/datasets/{did}/rankings?budget=4').json()
        assert scored['ground_truth_available'] is True
        assert scored['review_budget']==4
        assert all(x['top_candidates'] for x in scored['strategies'])
        # Same audited findings on a real-data-designated collection cannot be scored using injected truth.
        with Session() as db:
            ds=db.get(Dataset,did);ds.synthetic=False;db.commit()
        unscored=c.get(f'/api/datasets/{did}/rankings?budget=6').json()
        assert unscored['ground_truth_available'] is False
        assert all(x['confirmed_known_defects'] is None for x in unscored['strategies'])
        assert all(x['top_candidates'] for x in unscored['strategies'])
        with Session() as db:
            ds=db.get(Dataset,did);ds.synthetic=True;db.commit()
        baseline=c.post(f'/api/datasets/{did}/experiments',json={'kind':'baseline','config':{'seed':42}}).json()
        run_job(c,baseline['job_id'])
        shortcut=c.post(f'/api/datasets/{did}/experiments',json={'kind':'shortcut','config':{}}).json()
        run_job(c,shortcut['job_id'])
        sample=c.get(f'/api/datasets/{did}/samples?size=1').json()['items'][0]
        counter=c.post(f'/api/datasets/{did}/experiments',json={'kind':'counterfactual','config':{'sample_id':sample['id'],'strength':.7}}).json()
        run_job(c,counter['job_id'])
        res=c.get('/api/experiments/'+counter['experiment_id']).json()['result']
        assert res['strength']==.7 and len(res['variants'])==4
        assert c.get('/artifacts/'+res['variants'][0]['image_path']).status_code==200
        assert c.get('/api/privacy').json()['token_required'] is False
