"""Persistent database-backed local worker; designed for one CPU task at a time."""
from __future__ import annotations
import threading,time,logging
from datetime import timedelta
from sqlalchemy import select
from .db import Session,Job,AuditRun,Experiment,now
from .analysis_engine import audit
from .labs import EXPERIMENT_RUNNERS

class Cancelled(Exception):pass

def recover_jobs():
    """On a single-workstation restart, no previous in-process job can still run.

    Recover all interrupted running jobs, not only those older than ten minutes.
    Otherwise a quick restart leaves jobs stuck forever in 'running'.
    """
    with Session() as db:
        stale=db.scalars(select(Job).where(Job.status=='running')).all()
        for j in stale:
            j.status='queued';j.progress=0;j.error=None
            j.message='Requeued after a previous worker stopped'
            j.updated_at=now()
            item=db.get(AuditRun,j.target_id) if j.kind=='audit' else db.get(Experiment,j.target_id)
            if item:item.status='queued';item.finished_at=None
        db.commit()

def run_one():
    with Session() as db:
        stmt=select(Job).where(Job.status=='queued').order_by(Job.created_at).limit(1)
        if db.bind.dialect.name=='postgresql':stmt=stmt.with_for_update(skip_locked=True)
        job=db.scalars(stmt).first()
        if not job:return False
        jid=job.id;kind=job.kind;target_id=job.target_id
        job.status='running';job.progress=1;job.message='Preparing research analysis';job.updated_at=now()
        db.commit()
    def progress(percent,message):
        with Session() as db:
            j=db.get(Job,jid)
            if not j or j.status=='cancelled':raise Cancelled('Job cancelled by user')
            j.progress=max(0,min(100,int(percent)));j.message=str(message)[:240];j.updated_at=now();db.commit()
    try:
        if kind=='audit':
            with Session() as db:
                r=db.get(AuditRun,target_id)
                if r:r.status='running';db.commit()
            with Session() as db:
                run=db.get(AuditRun,target_id)
                if not run:raise ValueError('Missing audit run')
                did=run.dataset_id
            audit(did,target_id,progress)
        elif kind in EXPERIMENT_RUNNERS:
            with Session() as db:
                e=db.get(Experiment,target_id)
                if not e:raise ValueError('Missing experiment')
                e.status='running';db.commit()
            EXPERIMENT_RUNNERS[kind](target_id,progress)
        else:raise ValueError('Unknown job type: '+kind)
        progress(100,'Completed successfully')
        with Session() as db:
            j=db.get(Job,jid);j.status='completed';db.commit()
    except Cancelled:
        with Session() as db:
            j=db.get(Job,jid);j.status='cancelled';j.message='Cancelled by user'
            item=db.get(AuditRun,target_id) if kind=='audit' else db.get(Experiment,target_id)
            if item:item.status='cancelled'
            db.commit()
    except Exception as ex:
        with Session() as db:
            j=db.get(Job,jid);j.status='failed';j.message='Analysis failed';j.error=f'{type(ex).__name__}: {str(ex)}'[:1000];j.updated_at=now()
            item=db.get(AuditRun,target_id) if kind=='audit' else db.get(Experiment,target_id)
            if item:item.status='failed'
            db.commit()
    return True

def loop(stop=None,delay=.8):
    recover_jobs()
    while stop is None or not stop.is_set():
        try:busy=run_one()
        except Exception:
            logging.exception('MedData background worker encountered an unexpected loop error')
            busy=False
        if not busy:
            if stop is not None:stop.wait(delay)
            else:time.sleep(delay)

if __name__=='__main__':
    print('MedData worker active. Stop with Ctrl+C.');loop()
