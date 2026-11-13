"""Synthetic regressions: multiclass CPU baseline and honest Evidence Graph states."""
import io
from types import SimpleNamespace

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend import labs
from backend.api import app
from backend.analysis_engine import forensic_graph
from backend.db import Session, Dataset, Sample, AuditRun, Finding
from backend.worker import run_one


def _finish_job(client, job_id):
    for _ in range(7):
        state = client.get(f"/api/jobs/{job_id}").json()
        if state["status"] in ("completed", "failed", "cancelled"):
            break
        assert run_one()
    final = client.get(f"/api/jobs/{job_id}").json()
    assert final["status"] == "completed", final
    return final


def test_baseline_model_handles_three_classes(monkeypatch):
    sample_rows = [
        SimpleNamespace(relpath=str(i), label=f"class_{i % 3}")
        for i in range(36)
    ]
    def features(path):
        index=int(path)
        category=index % 3
        vector=np.zeros(6, dtype=float)
        vector[category]=3.0
        vector[3:]=((index % 7) / 100, (index % 5) / 100, 1.0)
        return vector
    monkeypatch.setattr(labs, "safe_path", lambda value: value)
    monkeypatch.setattr(labs, "extract_features", features)
    fitted=labs._model(sample_rows, seed=42)
    assert len(fitted.classes_) == 3
    probabilities=fitted.predict_proba(np.vstack([features(str(i)) for i in range(3)]))
    assert probabilities.shape == (3, 3)
    np.testing.assert_allclose(probabilities.sum(axis=1), np.ones(3), rtol=1e-6)


@pytest.fixture
def multiclass_archive():
    rng=np.random.default_rng(42)
    arrays={}
    for split, count in (("train", 36), ("val", 12), ("test", 12)):
        labels=np.arange(count,dtype=np.int64)%3
        images=np.empty((count,28,28,3),dtype=np.uint8)
        for i,label in enumerate(labels):
            image=rng.integers(0,20,(28,28,3),dtype=np.uint8)
            image[:,:,int(label)] += 185
            images[i]=image
        arrays[f"{split}_images"]=images
        arrays[f"{split}_labels"]=labels[:,None]
    out=io.BytesIO()
    np.savez_compressed(out,**arrays)
    out.seek(0)
    return out


def test_multiclass_import_audit_baseline_and_graph(multiclass_archive):
    """Exercise a three-class biomedical-style array with synthetic images only."""
    with TestClient(app) as client:
        response=client.post("/api/datasets/import",data={
            "name":"Synthetic 3 class CPU regression",
            "source":"Generated test arrays",
            "license":"Synthetic test only",
            "max_per_split":"50",
        },files={"file":("three_class.npz",multiclass_archive,"application/octet-stream")})
        assert response.status_code==200,response.text
        dataset_id=response.json()["dataset_id"]
        a=client.post(f"/api/datasets/{dataset_id}/audit")
        assert a.status_code==200,a.text
        _finish_job(client,a.json()["job_id"])
        detail=client.get(f"/api/datasets/{dataset_id}").json()
        completed=next(x for x in detail["audits"] if x["status"]=="completed")
        label_info=completed["summary"]["label_analysis"]
        assert label_info["evaluated"]==36, label_info
        before=client.get(f"/api/datasets/{dataset_id}/graph").json()
        assert before["audit_completed"]
        assert before["nodes"]
        assert all(edge["source"].startswith("f:") and edge["target"].startswith("s:") for edge in before["edges"])
        training=client.post(f"/api/datasets/{dataset_id}/experiments",json={
            "kind":"baseline","config":{"seed":42}})
        assert training.status_code==200,training.text
        _finish_job(client,training.json()["job_id"])
        experiment=client.get("/api/experiments/"+training.json()["experiment_id"]).json()
        assert experiment["status"]=="completed"
        assert experiment["result"]["test"]["metrics"]["n"]>0
        assert len(experiment["result"]["test"]["metrics"]["labels"])==3


def test_global_audit_findings_preserve_isolated_real_samples():
    """An association with no sample_id may not create phantom edges or a blank graph."""
    with Session() as db:
        dataset=Dataset(name="Synthetic graph-only regression",source="QA",
                        license="Test only",modality="Synthetic")
        db.add(dataset);db.flush()
        sample=Sample(dataset_id=dataset.id,sample_id="research_image_1",
                      relpath="not_read_by_graph.png",label="sample_label",
                      split="train",width=28,height=28)
        audit=AuditRun(dataset_id=dataset.id,status="completed")
        db.add_all([sample,audit]);db.flush()
        finding=Finding(dataset_id=dataset.id,audit_id=audit.id,
                        kind="source_association",title="Source-label association",
                        detail="Dataset-level hypothesis only",priority=0.8,
                        sample_id=None,linked_id=None)
        db.add(finding);db.commit()
        result=forensic_graph(db,dataset.id)
        assert result["audit_completed"] is True
        assert result["network_mode"]=="sample_inventory"
        assert result["edges"]==[]
        assert result["linked_finding_count"]==0
        assert {n["type"] for n in result["nodes"]}=={"sample","finding"}
        assert any(n["id"]=="s:"+sample.id for n in result["nodes"])
        assert any(n["id"]=="f:"+finding.id for n in result["nodes"])
        # Verify true detector links are exposed only after attaching evidence.
        finding.sample_id=sample.id
        db.commit()
        linked=forensic_graph(db,dataset.id)
        assert linked["network_mode"]=="evidence"
        assert linked["linked_finding_count"]==1
        assert linked["edges"]==[{"source":"f:"+finding.id,"target":"s:"+sample.id}]
