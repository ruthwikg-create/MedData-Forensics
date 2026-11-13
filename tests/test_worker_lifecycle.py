"""Job lifecycle regression checks for interrupted and cancelled local research tasks."""
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.api import app
from backend.db import Session, AuditRun, Experiment, Job
from backend.worker import recover_jobs, run_one


def _demo(client,seed):
    response=client.post('/api/datasets/demo',json={'seed':seed,'count':40})
    assert response.status_code==200,response.text
    return response.json()['dataset_id']


def test_cancel_queued_experiment_and_audit_together(monkeypatch):
    monkeypatch.setenv('MDF_NO_AUTOWORKER','1')
    with TestClient(app) as client:
        did=_demo(client,230)
        experiment=client.post(f'/api/datasets/{did}/experiments',
                               json={'kind':'baseline','config':{'seed':42}})
        assert experiment.status_code==200,experiment.text
        eid=experiment.json()['experiment_id']
        job=experiment.json()['job_id']
        cancelled=client.post(f'/api/jobs/{job}/cancel')
        assert cancelled.status_code==200,cancelled.text
        assert cancelled.json()['status']=='cancelled'
        with Session() as db:
            assert db.get(Experiment,eid).status=='cancelled'
        assert client.post(f'/api/jobs/{job}/cancel').status_code==409

        audit=client.post(f'/api/datasets/{did}/audit')
        assert audit.status_code==200,audit.text
        jid=audit.json()['job_id']
        response=client.post(f'/api/jobs/{jid}/cancel')
        assert response.status_code==200,response.text
        with Session() as db:
            j=db.get(Job,jid)
            target=db.get(AuditRun,j.target_id)
            assert j.status=='cancelled'
            assert target.status=='cancelled'


def test_fast_restart_requeues_recent_running_job_and_target(monkeypatch):
    monkeypatch.setenv('MDF_NO_AUTOWORKER','1')
    with TestClient(app) as client:
        did=_demo(client,231)
        result=client.post(f'/api/datasets/{did}/experiments',json={'kind':'baseline','config':{}})
        assert result.status_code==200,result.text
        eid,jid=result.json()['experiment_id'],result.json()['job_id']
        with Session() as db:
            e,j=db.get(Experiment,eid),db.get(Job,jid)
            e.status='running'
            j.status='running'
            j.progress=55
            j.message='Extracting features'
            # The timestamp remains recent: recovery must not wait 10 minutes.
            db.commit()
        recover_jobs()
        with Session() as db:
            e,j=db.get(Experiment,eid),db.get(Job,jid)
            assert j.status=='queued'
            assert j.progress==0
            assert e.status=='queued'
            assert 'Recovered after' in j.message
        assert run_one()
        completed=client.get(f'/api/jobs/{jid}').json()
        assert completed['status']=='completed',completed


def test_restart_reconciles_completed_target_without_reexecuting(monkeypatch):
    monkeypatch.setenv('MDF_NO_AUTOWORKER','1')
    with TestClient(app) as client:
        did=_demo(client,232)
        result=client.post(f'/api/datasets/{did}/experiments',json={'kind':'baseline','config':{}})
        assert result.status_code==200,result.text
        eid,jid=result.json()['experiment_id'],result.json()['job_id']
        with Session() as db:
            e,j=db.get(Experiment,eid),db.get(Job,jid)
            e.status='completed'
            e.result='{"test":{"metrics":{"n":1}}}'
            j.status='running'
            db.commit()
        recover_jobs()
        with Session() as db:
            e,j=db.get(Experiment,eid),db.get(Job,jid)
            assert e.status=='completed'
            assert j.status=='completed'
            assert j.progress==100
            assert 'Recovered completed result' in j.message
