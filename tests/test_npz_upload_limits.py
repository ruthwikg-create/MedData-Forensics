"""Upload-size regression checks for biomedical NPZ imports; generated arrays only."""
import io

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend import api, ingest, security


@pytest.fixture
def sample_npz():
    rng = np.random.default_rng(42)
    out = io.BytesIO()
    sizes = {"train": 24, "val": 8, "test": 8}
    data = {}
    for split, n in sizes.items():
        data[f"{split}_images"] = rng.integers(0, 256, size=(n, 28, 28, 3), dtype=np.uint8)
        data[f"{split}_labels"] = np.asarray([[i % 2] for i in range(n)], dtype=np.int64)
    np.savez_compressed(out, **data)
    return out.getvalue()


def test_npz_cap_accepts_valid_archive_larger_than_zip_cap(monkeypatch, sample_npz):
    # Use a small test-only ZIP cap, not a 150 MiB allocation, to verify separate limits.
    zip_cap = 4096
    assert len(sample_npz) > zip_cap
    assert security.MAX_NPZ_BYTES > security.MAX_ARCHIVE_BYTES
    monkeypatch.setattr(api, "MAX_ARCHIVE_BYTES", zip_cap)
    monkeypatch.setattr(ingest, "MAX_ARCHIVE_BYTES", zip_cap)

    with TestClient(api.app) as client:
        response = client.post(
            "/api/datasets/import",
            data={"name": "NPZ size-boundary regression", "source": "Generated test arrays",
                  "license": "Test data only", "max_per_split": "10"},
            files={"file": ("pathmnist.npz", sample_npz, "application/octet-stream")},
        )
        assert response.status_code == 200, response.text
        did = response.json()["dataset_id"]
        detail = client.get(f"/api/datasets/{did}").json()
        assert detail["splits"] == {"train": 10, "val": 8, "test": 8}
        assert detail["dataset"]["synthetic"] is False


def test_zip_retains_stricter_cap(monkeypatch):
    monkeypatch.setattr(api, "MAX_ARCHIVE_BYTES", 4096)
    with TestClient(api.app) as client:
        response = client.post(
            "/api/datasets/import",
            data={"name": "Oversized ZIP"},
            files={"file": ("images.zip", b"PK" + b"x" * 5000, "application/zip")},
        )
    assert response.status_code == 413
    assert "150 MiB" in response.json()["detail"]


def test_npz_still_rejects_oversized_archive(monkeypatch, sample_npz):
    monkeypatch.setattr(api, "MAX_NPZ_BYTES", 4096)
    with TestClient(api.app) as client:
        response = client.post(
            "/api/datasets/import",
            data={"name": "Oversized NPZ"},
            files={"file": ("too_large.npz", sample_npz, "application/octet-stream")},
        )
    assert response.status_code == 413
    assert "256 MiB" in response.json()["detail"]


def test_importer_enforces_npz_limit_independently(monkeypatch, tmp_path, sample_npz):
    source = tmp_path / "large.npz"
    source.write_bytes(sample_npz)
    monkeypatch.setattr(ingest, "MAX_NPZ_BYTES", 4096)
    with pytest.raises(ValueError, match="256 MiB safety cap"):
        ingest.import_npz(source, "Overflow", max_samples_per_split=10)
