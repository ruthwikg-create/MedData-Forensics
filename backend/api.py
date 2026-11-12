"""Local-first FastAPI research workbench. Does not provide medical diagnosis."""
from __future__ import annotations
from collections import Counter,defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional,Literal
from datetime import datetime,timezone
import csv,io,json,os,shutil,tempfile,threading,html
from fastapi import FastAPI,HTTPException,UploadFile,File,Form,Request,Query
from fastapi.responses import FileResponse,HTMLResponse,JSONResponse,StreamingResponse,Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from sqlalchemy import select,func
from .db import Session,DATA_ROOT,ARTIFACT_ROOT,Dataset,Sample,Finding,Review,AuditRun,Experiment,Job,jd,jl,now
from .security import safe_path,extract_auth,MAX_ARCHIVE_BYTES
from .ingest import demo_dataset,import_zip,import_npz
from .analysis_engine import forensic_graph,ranking_comparison
from .labs import EXPERIMENT_RUNNERS
from .worker import loop

stop=threading.Event()
thread=None
@asynccontextmanager
async def lifespan(app):
    global thread
    stop.clear()
    if os.getenv('MDF_NO_AUTOWORKER','0')!='1':
        thread=threading.Thread(target=loop,args=(stop,),daemon=True,name='mdf-worker');thread.start()
    yield
    stop.set()
    if thread:thread.join(timeout=3)
app=FastAPI(title='MedData Forensics',version='0.8.1-research',lifespan=lifespan,docs_url='/api/docs',openapi_url='/api/openapi.json')

@app.middleware('http')
async def security_middleware(request,call_next):
    if request.url.path.startswith('/api') or request.url.path.startswith('/files') or request.url.path.startswith('/artifacts'):
        if request.url.path != '/api/session' and not extract_auth(request):return JSONResponse({'detail':'Invalid local access token'},status_code=401)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store'
    return response

class DemoInput(BaseModel):
    seed:int=Field(42,ge=1,le=999999)
    count:int=Field(128,ge=40,le=1200)
class ReviewInput(BaseModel):
    reviewer:str=Field('Local researcher',min_length=2,max_length=100)
    decision:Literal['confirmed','rejected','uncertain']
    notes:str=Field('',max_length=4000)
    duration_seconds:float|None=Field(default=None,ge=0,le=86400)
class ExperimentInput(BaseModel):
    kind:Literal['baseline','shortcut','counterfactual','cross_dataset','impact','scenario']
    config:dict=Field(default_factory=dict)


def stamp(dt):return dt.isoformat()+'Z' if dt else None

def sample_out(s):
    return {'id':s.id,'sample_id':s.sample_id,'label':s.label,'split':s.split,'group_id':s.group_id,'group_type':s.group_type,
      'site':s.site,'sha256':s.sha256,'phash':s.phash,'width':s.width,'height':s.height,'metadata':jl(s.meta),'image_url':'/files/'+s.id}

def dataset_out(d,count=0):
    return {'id':d.id,'name':d.name,'source':d.source,'source_url':d.source_url,'license':d.license,'modality':d.modality,
      'description':d.description,'synthetic':bool(d.synthetic),'created_at':stamp(d.created_at),
      'manifest_hash':d.manifest_hash,'parent_id':d.parent_id,'metadata':jl(d.meta),'sample_count':count}

def finding_out(f):
    return {'id':f.id,'kind':f.kind,'severity':f.severity,'status':f.status,'title':f.title,'detail':f.detail,
      'confidence':f.confidence,'priority':f.priority,'cost':f.cost,'sample_id':f.sample_id,'linked_id':f.linked_id,
      'audit_id':f.audit_id,'created_at':stamp(f.created_at),'detector':f.detector,'evidence':jl(f.evidence)}

def experiment_out(e):
    return {'id':e.id,'dataset_id':e.dataset_id,'kind':e.kind,'status':e.status,'config':jl(e.config),'result':jl(e.result),
      'created_at':stamp(e.created_at),'finished_at':stamp(e.finished_at)}

def get_dataset(db,id):
    item=db.get(Dataset,id)
    if not item:raise HTTPException(404,'Dataset not found')
    return item

def _enqueue(db,kind,target_id):
    job=Job(kind=kind,target_id=target_id,status='queued',progress=0)
    db.add(job);db.flush();return job

@app.post('/api/session')
def authorize_session(request:Request):
    if not extract_auth(request):raise HTTPException(401,'Incorrect local access token')
    response=JSONResponse({'authenticated':True,'message':'Local access granted for this browser session'})
    if os.getenv('MDF_ACCESS_TOKEN'):
        response.set_cookie('mdf_access',os.getenv('MDF_ACCESS_TOKEN'),httponly=True,samesite='strict',secure=False,path='/',max_age=8*3600)
    return response

@app.get('/api/health')
def health():
    return {'status':'ok','version':'0.8.0-research','analysis':'local research only','worker_enabled':os.getenv('MDF_NO_AUTOWORKER','0')!='1','storage':str(DATA_ROOT)}

@app.get('/api/overview')
def overview():
    with Session() as db:
        return {'datasets':db.scalar(select(func.count(Dataset.id))),
          'samples':db.scalar(select(func.count(Sample.id))),
          'findings':db.scalar(select(func.count(Finding.id))),
          'reviewed':db.scalar(select(func.count(Finding.id)).where(Finding.status!='suspected')),
          'experiments':db.scalar(select(func.count(Experiment.id))),
          'recent_jobs':[job_out(j) for j in db.scalars(select(Job).order_by(Job.created_at.desc()).limit(8))],
          'recent_datasets':[dataset_out(d,db.scalar(select(func.count(Sample.id)).where(Sample.dataset_id==d.id))) for d in db.scalars(select(Dataset).order_by(Dataset.created_at.desc()).limit(6))]}

@app.get('/api/datasets')
def datasets():
    with Session() as db:
        counts=dict(db.execute(select(Sample.dataset_id,func.count(Sample.id)).group_by(Sample.dataset_id)).all())
        return [dataset_out(d,counts.get(d.id,0)) for d in db.scalars(select(Dataset).order_by(Dataset.created_at.desc())).all()]

@app.post('/api/datasets/demo')
def add_demo(payload:DemoInput):
    return {'dataset_id':demo_dataset(payload.seed,payload.count),'message':'Generated synthetic geometry, not clinical images'}

@app.post('/api/datasets/import')
async def import_dataset(file:UploadFile=File(...),name:str=Form(...),source:str=Form('Local upload'),license:str=Form('Unspecified; verify authorization'),modality:str=Form('Biomedical 2D image'),max_per_split:int=Form(2000)):
    if len(name.strip())<2 or len(name)>200:raise HTTPException(422,'Dataset name must have 2–200 characters')
    filename=(file.filename or '').lower()
    if not filename.endswith(('.npz','.zip')):raise HTTPException(415,'Upload a MedMNIST .npz or .zip containing samples.csv and images')
    suffix=Path(filename).suffix
    p=None
    try:
        with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as f:
            p=Path(f.name);size=0
            while True:
                chunk=await file.read(1024*1024)
                if not chunk:break
                size+=len(chunk)
                if size>MAX_ARCHIVE_BYTES:raise HTTPException(413,'Dataset package exceeds local upload cap (150 MB)')
                f.write(chunk)
        try:
            if suffix=='.npz':did=import_npz(p,name,source,license,max_per_split)
            else:did=import_zip(p,name,source,license,modality)
            return {'dataset_id':did,'message':'Imported locally; verify source license and group metadata.'}
        except (ValueError,OSError,KeyError) as ex:raise HTTPException(422,str(ex))
    finally:
        if p:p.unlink(missing_ok=True)
        await file.close()

@app.get('/api/datasets/{did}')
def dataset_detail(did:str):
    with Session() as db:
        d=get_dataset(db,did)
        rows=db.scalars(select(Sample).where(Sample.dataset_id==did)).all()
        audits=db.scalars(select(AuditRun).where(AuditRun.dataset_id==did).order_by(AuditRun.created_at.desc())).all()
        experiments=db.scalars(select(Experiment).where(Experiment.dataset_id==did).order_by(Experiment.created_at.desc())).all()
        return {'dataset':dataset_out(d,len(rows)),
            'splits':dict(Counter(s.split for s in rows)),'labels':dict(Counter(s.label for s in rows)),
            'groups_with_ids':sum(bool(s.group_id) for s in rows),'sites':dict(Counter(s.site or 'unknown' for s in rows)),
            'audits':[{'id':a.id,'status':a.status,'summary':jl(a.summary),'created_at':stamp(a.created_at)} for a in audits],
            'experiments':[experiment_out(e) for e in experiments]}

@app.get('/api/datasets/{did}/dna')
def dataset_dna(did:str):
    with Session() as db:
        d=get_dataset(db,did)
        rows=db.scalars(select(Sample).where(Sample.dataset_id==did)).all()
        lineage=[];seen=set();current=d
        while current and current.id not in seen:
            seen.add(current.id);lineage.append({'id':current.id,'name':current.name,'manifest_hash':current.manifest_hash,'parent_id':current.parent_id})
            current=db.get(Dataset,current.parent_id) if current.parent_id else None
        return {'dataset':dataset_out(d,len(rows)),'lineage':lineage,'splits':dict(Counter(s.split for s in rows)),
          'labels':dict(Counter(s.label for s in rows)),'sites':dict(Counter(s.site or 'unknown' for s in rows)),
          'image_shapes':dict(Counter(f'{s.width}×{s.height}' if s.width and s.height else 'unknown' for s in rows)),
          'group_coverage':{'with_group_id':sum(bool(s.group_id) for s in rows),'without_group_id':sum(not s.group_id for s in rows)},
          'source_notes':'Identifiers are interpreted only according to the dataset provider. Lesion IDs are not patient IDs.'}

@app.get('/api/datasets/{did}/samples')
def dataset_samples(did:str,page:int=Query(1,ge=1),size:int=Query(24,ge=1,le=100),split:str='',label:str='',search:str=''):
    with Session() as db:
        get_dataset(db,did)
        q=select(Sample).where(Sample.dataset_id==did)
        if split:q=q.where(Sample.split==split)
        if label:q=q.where(Sample.label==label)
        if search:q=q.where(Sample.sample_id.ilike(f'%{search[:100]}%'))
        count=db.scalar(select(func.count()).select_from(q.subquery()))
        rows=db.scalars(q.order_by(Sample.sample_id).offset((page-1)*size).limit(size)).all()
        return {'count':count,'page':page,'size':size,'items':[sample_out(s) for s in rows]}

@app.get('/api/samples/{sid}')
def sample_detail(sid:str):
    with Session() as db:
        s=db.get(Sample,sid)
        if not s:raise HTTPException(404,'Sample missing')
        findings=db.scalars(select(Finding).where((Finding.sample_id==sid)|(Finding.linked_id==sid)).order_by(Finding.priority.desc()).limit(50)).all()
        return {'sample':sample_out(s),'findings':[finding_out(x) for x in findings]}

@app.get('/files/{sid}')
def serve_image(sid:str):
    with Session() as db:
        s=db.get(Sample,sid)
        if not s:raise HTTPException(404,'Image not found')
        p=safe_path(s.relpath)
        if not p.is_file():raise HTTPException(404,'Image not found on disk')
        return FileResponse(p,headers={'Cache-Control':'private, no-store','Content-Security-Policy':"default-src 'none'"})

@app.get('/artifacts/{path:path}')
def serve_artifact(path:str):
    p=(ARTIFACT_ROOT/path).resolve()
    if not p.is_relative_to(ARTIFACT_ROOT) or not p.is_file() or p.suffix.lower() not in ('.png','.jpg','.json'):
        raise HTTPException(404,'Artifact not available')
    return FileResponse(p)

@app.post('/api/datasets/{did}/audit')
def start_audit(did:str):
    with Session() as db:
        get_dataset(db,did)
        run=AuditRun(dataset_id=did,config=jd({'detectors':['integrity','duplicates','near_duplicate','split_leakage','label_suspicion','source_association'],'thresholds':{'phash_distance':7,'ssim':.935}}))
        db.add(run);db.flush();job=_enqueue(db,'audit',run.id);db.commit()
        return {'audit_id':run.id,'job_id':job.id}

@app.get('/api/datasets/{did}/findings')
def dataset_findings(did:str,status:str='',kind:str='',page:int=Query(1,ge=1),size:int=Query(50,ge=1,le=200),order:str='priority'):
    with Session() as db:
        get_dataset(db,did);q=select(Finding).where(Finding.dataset_id==did)
        if status:q=q.where(Finding.status==status)
        if kind:q=q.where(Finding.kind==kind)
        # Most recent audit only, so repeated audits aren't double counted
        latest=db.scalar(select(AuditRun.id).where(AuditRun.dataset_id==did,AuditRun.status=='completed').order_by(AuditRun.created_at.desc()).limit(1))
        if latest:q=q.where(Finding.audit_id==latest)
        count=db.scalar(select(func.count()).select_from(q.subquery()))
        if order=='confidence':q=q.order_by(Finding.confidence.desc())
        elif order=='severity':q=q.order_by(Finding.severity.asc())
        else:q=q.order_by(Finding.priority.desc())
        rows=db.scalars(q.offset((page-1)*size).limit(size)).all()
        return {'count':count,'page':page,'size':size,'items':[finding_out(x) for x in rows]}

@app.get('/api/findings/{fid}')
def finding_detail(fid:str):
    with Session() as db:
        f=db.get(Finding,fid)
        if not f:raise HTTPException(404,'Finding missing')
        history=db.scalars(select(Review).where(Review.finding_id==fid).order_by(Review.created_at.desc())).all()
        return {'finding':finding_out(f),'sample':sample_out(db.get(Sample,f.sample_id)) if f.sample_id else None,
          'linked':sample_out(db.get(Sample,f.linked_id)) if f.linked_id else None,
          'reviews':[{'id':r.id,'reviewer':r.reviewer,'decision':r.decision,'notes':r.notes,'duration_seconds':r.duration_seconds,'created_at':stamp(r.created_at)} for r in history]}

@app.post('/api/findings/{fid}/review')
def review_finding(fid:str,payload:ReviewInput):
    with Session() as db:
        f=db.get(Finding,fid)
        if not f:raise HTTPException(404,'Finding not found')
        r=Review(finding_id=fid,reviewer=payload.reviewer,decision=payload.decision,notes=payload.notes,duration_seconds=payload.duration_seconds)
        f.status=payload.decision;db.add(r);db.commit()
        return {'finding_id':fid,'status':f.status,'review_id':r.id,'message':'Review recorded; image labels and source records were not changed.'}

@app.get('/api/datasets/{did}/graph')
def graph(did:str,limit:int=Query(100,ge=10,le=300)):
    with Session() as db:
        get_dataset(db,did);return forensic_graph(db,did,limit)

@app.get('/api/datasets/{did}/rankings')
def rankings(did:str,budget:int=Query(15,ge=1,le=500)):
    with Session() as db:
        get_dataset(db,did);return ranking_comparison(db,did,budget)

@app.post('/api/datasets/{did}/experiments')
def create_experiment(did:str,payload:ExperimentInput):
    with Session() as db:
        get_dataset(db,did)
        if payload.kind not in EXPERIMENT_RUNNERS:raise HTTPException(422,'Unsupported experiment')
        e=Experiment(dataset_id=did,kind=payload.kind,config=jd(payload.config))
        db.add(e);db.flush();job=_enqueue(db,payload.kind,e.id);db.commit()
        return {'experiment_id':e.id,'job_id':job.id}

@app.get('/api/experiments/{eid}')
def experiment_detail(eid:str):
    with Session() as db:
        e=db.get(Experiment,eid)
        if not e:raise HTTPException(404,'Experiment not found')
        return experiment_out(e)

def job_out(j):
    return {'id':j.id,'target_id':j.target_id,'kind':j.kind,'status':j.status,'progress':j.progress,'message':j.message,'error':j.error,
      'created_at':stamp(j.created_at),'updated_at':stamp(j.updated_at)}
@app.get('/api/jobs')
def jobs():
    with Session() as db:return [job_out(j) for j in db.scalars(select(Job).order_by(Job.created_at.desc()).limit(35)).all()]
@app.get('/api/jobs/{jid}')
def job_detail(jid:str):
    with Session() as db:
        j=db.get(Job,jid)
        if not j:raise HTTPException(404,'Job not found')
        return job_out(j)
@app.post('/api/jobs/{jid}/cancel')
def cancel_job(jid:str):
    with Session() as db:
        j=db.get(Job,jid)
        if not j:raise HTTPException(404,'Job not found')
        if j.status not in ('running','queued'):raise HTTPException(409,'Job is not active')
        j.status='cancelled';j.message='Cancellation requested';db.commit()
        return job_out(j)

@app.get('/api/datasets/{did}/report')
def download_report(did:str,format:str='json'):
    with Session() as db:
        d=get_dataset(db,did)
        latest=db.scalar(select(AuditRun).where(AuditRun.dataset_id==did,AuditRun.status=='completed').order_by(AuditRun.created_at.desc()).limit(1))
        rows=db.scalars(select(Finding).where(Finding.audit_id==latest.id)).all() if latest else []
        reviews=db.scalars(select(Review).where(Review.finding_id.in_([x.id for x in rows]))).all() if rows else []
        experiments=db.scalars(select(Experiment).where(Experiment.dataset_id==did,Experiment.status=='completed')).all()
        content={'app':'MedData Forensics','research_only':True,'generated_utc':now().isoformat(),
           'dataset':dataset_out(d,db.scalar(select(func.count(Sample.id)).where(Sample.dataset_id==did))),
           'audit_summary':jl(latest.summary) if latest else None,
           'findings':[finding_out(f) for f in rows],
           'reviews':[{'finding_id':r.finding_id,'reviewer':r.reviewer,'decision':r.decision,'notes':r.notes,'timestamp':stamp(r.created_at)} for r in reviews],
           'experiments':[experiment_out(e) for e in experiments],
           'limitations':['Automated flags are investigative hypotheses, not clinical ground truth.','Group overlap requires documented group-identifier semantics.','Benchmarks using synthetic defects do not establish performance on natural medical data.'],
           'methods':'SHA256/pixel hashing, perceptual hash+SSIM, source association, OOF label suspicion, bounded CPU model evaluations',
           'claim':'No clinical or external validation has been performed by this product.'}
        fname='MedData_Forensics_'+did
        if format=='json':return Response(json.dumps(content,indent=2,default=str),media_type='application/json',headers={'Content-Disposition':f'attachment; filename={fname}.json'})
        if format=='csv':
            output=io.StringIO();writer=csv.DictWriter(output,fieldnames=['id','kind','severity','status','title','confidence','priority','sample_id','linked_id'])
            writer.writeheader();writer.writerows([{k:getattr(f,k) for k in writer.fieldnames} for f in rows])
            return Response(output.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename={fname}.csv'})
        if format=='html':
            esc=html.escape
            details=''.join(f'<tr><td>{esc(f.kind)}</td><td>{esc(f.title)}</td><td>{esc(f.status)}</td><td>{f.confidence:.2f}</td></tr>' for f in rows)
            page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Research audit {esc(d.name)}</title><style>body{{font:16px system-ui;max-width:920px;margin:50px auto;color:#17262f;padding:24px}}th,td{{border-bottom:1px solid #ddd;text-align:left;padding:10px}}table{{width:100%}}small{{color:#596c74}}</style><h1>MedData Forensics — research audit</h1><p><b>{esc(d.name)}</b> · {esc(d.source)} · {esc(d.license)}</p><p>Manifest SHA256: <code>{esc(d.manifest_hash)}</code></p><h2>Investigative findings ({len(rows)})</h2><table><tr><th>Type</th><th>Observation</th><th>Review status</th><th>Confidence</th></tr>{details}</table><h2>Interpretation limits</h2><p>Automated flags are hypotheses for review. This report does not validate medical diagnoses, clinical performance or regulatory compliance.</p><small>Generated {esc(now().isoformat())}</small></html>'''
            return Response(page,media_type='text/html',headers={'Content-Disposition':f'attachment; filename={fname}.html'})
        raise HTTPException(400,'format must be json, csv, html')

@app.get('/api/privacy')
def privacy():
    return {'processing':'local only','outbound_api_calls':False,'telemetry':False,'public_data_hosting':False,
      'storage':'data/ and artifacts/ outside frontend web root','database':'local SQLite default; PostgreSQL optional',
      'uploads':'150 MB archives maximum; extension, size, archive traversal checks','authentication':'optional MDF_ACCESS_TOKEN; bind to 127.0.0.1 unless configured',
      'clinical_data_policy':'Use only authorized, de-identified or synthetic research data. No clinical care.'}

STATIC=Path(__file__).resolve().parents[1]/'frontend'/'static'
app.mount('/assets',StaticFiles(directory=STATIC),name='assets')
@app.get('/')
def home():return FileResponse(STATIC/'index.html')
