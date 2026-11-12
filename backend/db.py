"""Local-first metadata database; PostgreSQL URL supported, SQLite works out of box."""
from __future__ import annotations
import os, json, uuid
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean, Index, event
from sqlalchemy.orm import declarative_base, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.getenv('MDF_DATA_DIR', str(ROOT / 'data'))).resolve()
ARTIFACT_ROOT = Path(os.getenv('MDF_ARTIFACT_DIR', str(ROOT / 'artifacts'))).resolve()
for directory in [DATA_ROOT, ARTIFACT_ROOT]:
    directory.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DATA_ROOT / "meddata.db"}')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)
if DATABASE_URL.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def _pragma(dbapi_connection, _):
        cur = dbapi_connection.cursor(); cur.execute('PRAGMA journal_mode=WAL'); cur.execute('PRAGMA foreign_keys=ON'); cur.close()
Session = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
Base = declarative_base()

def uid(): return uuid.uuid4().hex[:16]
def now(): return datetime.now(timezone.utc)
def jd(x): return json.dumps(x, ensure_ascii=False, allow_nan=False, default=str)
def jl(x, default=None):
    try: return json.loads(x) if x else (default if default is not None else {})
    except (TypeError, ValueError): return default if default is not None else {}

class Dataset(Base):
    __tablename__='datasets'
    id=Column(String(16),primary_key=True,default=uid)
    name=Column(String(200), nullable=False)
    source=Column(String(255),nullable=False,default='local')
    source_url=Column(Text,nullable=False,default='')
    license=Column(String(250),nullable=False,default='Unspecified; verify before use')
    modality=Column(String(120),nullable=False,default='biomedical research image')
    description=Column(Text,default='')
    synthetic=Column(Boolean,default=False)
    created_at=Column(DateTime(timezone=True),default=now)
    manifest_hash=Column(String(64),default='')
    parent_id=Column(String(16),nullable=True)
    meta=Column(Text,default='{}')

class Sample(Base):
    __tablename__='samples'
    id=Column(String(16),primary_key=True,default=uid)
    dataset_id=Column(String(16),ForeignKey('datasets.id',ondelete='CASCADE'),nullable=False,index=True)
    sample_id=Column(String(200),nullable=False)
    relpath=Column(String(700),nullable=False)
    label=Column(String(120),nullable=False)
    split=Column(String(30),nullable=False,default='train')
    group_id=Column(String(160),nullable=True)
    group_type=Column(String(60),nullable=True)
    site=Column(String(100),nullable=True)
    source_id=Column(String(200),nullable=True)
    sha256=Column(String(64),nullable=True)
    pixelhash=Column(String(64),nullable=True)
    phash=Column(String(40),nullable=True)
    width=Column(Integer,nullable=True)
    height=Column(Integer,nullable=True)
    meta=Column(Text,default='{}')
    __table_args__=(Index('ix_sample_ds_split','dataset_id','split'),)

class AuditRun(Base):
    __tablename__='audit_runs'
    id=Column(String(16),primary_key=True,default=uid)
    dataset_id=Column(String(16),ForeignKey('datasets.id'),nullable=False,index=True)
    status=Column(String(30),default='queued')
    config=Column(Text,default='{}')
    summary=Column(Text,default='{}')
    created_at=Column(DateTime(timezone=True),default=now)
    finished_at=Column(DateTime(timezone=True),nullable=True)

class Finding(Base):
    __tablename__='findings'
    id=Column(String(16),primary_key=True,default=uid)
    dataset_id=Column(String(16),ForeignKey('datasets.id'),nullable=False,index=True)
    audit_id=Column(String(16),ForeignKey('audit_runs.id'),nullable=False,index=True)
    kind=Column(String(80),nullable=False)
    severity=Column(String(25),default='medium')
    status=Column(String(30),default='suspected')
    sample_id=Column(String(16),ForeignKey('samples.id'),nullable=True)
    linked_id=Column(String(16),ForeignKey('samples.id'),nullable=True)
    confidence=Column(Float,default=0.5)
    priority=Column(Float,default=0)
    cost=Column(Float,default=1)
    title=Column(String(200),nullable=False)
    detail=Column(Text,default='')
    evidence=Column(Text,default='{}')
    detector=Column(String(60),default='')
    created_at=Column(DateTime(timezone=True),default=now)

class Review(Base):
    __tablename__='reviews'
    id=Column(String(16),primary_key=True,default=uid)
    finding_id=Column(String(16),ForeignKey('findings.id'),nullable=False,index=True)
    reviewer=Column(String(100),nullable=False)
    decision=Column(String(25),nullable=False)
    notes=Column(Text,default='')
    duration_seconds=Column(Float,nullable=True)
    created_at=Column(DateTime(timezone=True),default=now)

class Experiment(Base):
    __tablename__='experiments'
    id=Column(String(16),primary_key=True,default=uid)
    dataset_id=Column(String(16),ForeignKey('datasets.id'),nullable=False,index=True)
    kind=Column(String(60),nullable=False)
    status=Column(String(30),default='queued')
    config=Column(Text,default='{}')
    result=Column(Text,default='{}')
    created_at=Column(DateTime(timezone=True),default=now)
    finished_at=Column(DateTime(timezone=True),nullable=True)

class Job(Base):
    __tablename__='jobs'
    id=Column(String(16),primary_key=True,default=uid)
    target_id=Column(String(16),nullable=False)
    kind=Column(String(40),nullable=False)
    status=Column(String(20),default='queued',index=True)
    progress=Column(Integer,default=0)
    message=Column(Text,default='Queued for analysis')
    error=Column(Text,nullable=True)
    created_at=Column(DateTime(timezone=True),default=now)
    updated_at=Column(DateTime(timezone=True),default=now)

Base.metadata.create_all(bind=engine)
