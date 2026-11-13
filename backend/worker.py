"""Persistent database-backed local worker; designed for one CPU task at a time."""
from __future__ import annotations
import threading,time,traceback
from datetime import timedelta
from sqlalchemy import select
from .db import Session,Job,AuditRun,Experiment,now
from .analysis_engine import audit
from .labs import EXPERIMENT_RUNNERS

class Cancelled(Exception):pass

def recover_jobs():
    """Reconcile jobs left running when the previous single local worker stopped.

    Recovery occurs at worker startup, not after an arbitrary timeout. Completed
    targets are never rerun (which might duplicate derived datasets or exports).
    The app is designed for one local worker, not parallel distributed workers.
    """
    with Session() as db:
        interrupted=db.scalars(select(Job).where(Job.status=='running')).all()
        for job in interrupted:
            target=(db.get(AuditRun,job.target_id) if job.kind=='audit'
                    else db.get(Experiment,job.target_id))
            if target and target.status in ('completed','failed','cancelled'):
                job.status=target.status
                job.message=('Recovered completed result' if target.status=='completed'
                             else 'Reconciled interrupted '+target.status+' task')
                job.progress=100 if target.status=='completed' else min(99,job.progress or 0)
                if target.status=='failed' and not job.error:
                    job.error='The interrupted analysis is recorded as failed; inspect the experiment and retry.'
            elif target:
                job.status='queued'
                job.progress=0
                job.message='Recovered after local worker restart; queued to retry'
                job.error=None
                target.status='queued'
            else:
                job.status='failed'
                job.message='Analysis target missing after restart'
                job.error='Cannot resume: the associated audit or experiment record no longer exists.'
            job.updated_at=now()
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
            busy=False
        if not busy:
            if stop is not None:stop.wait(delay)
            else:time.sleep(delay)

if __name__=='__main__':
    print('MedData worker active. Stop with Ctrl+C.');loop()
