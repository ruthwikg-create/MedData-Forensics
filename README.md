# MedData Forensics

**Local-first biomedical AI dataset investigation and reproducibility workbench.**

> **RESEARCH ONLY.** This software does not diagnose patients, establish image-label truth, certify a medical device, validate a model for clinical use, or establish a dataset's clinical suitability. All new/demo test results refer only to synthetic geometric phantoms unless a dataset is explicitly identified as an independently sourced research dataset. No real-world model validation or accepted research-paper contribution is claimed.

MedData Forensics imports image classification datasets, identifies potential data-integrity risks with inspectable evidence, lets researchers review findings, and runs CPU-friendly comparative experiments. Every original dataset remains unchanged. No medical equipment, CUDA GPU, Docker or paid API required.

## Quick start: Windows 11

Prerequisite: **Python 3.11+** (your Python 3.11.9 is suitable), internet access once to install free packages, and sufficient storage. The first sandbox uses newly generated shapes (not clinical images).

Simplest option: double-click **`RUN_ME_WINDOWS.bat`**. It sets up free Python packages on first launch and starts the local server. Alternatively, open PowerShell from the unzipped folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Setup-Windows.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Start-Windows.ps1
```

Then open **http://127.0.0.1:8765**. Press `Ctrl+C` in PowerShell to stop the server.

Equivalent manual setup:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe start.py
```

The application creates `data/meddata.db` automatically. It uses SQLite to work immediately without a database server. PostgreSQL 18 is supported as an optional alternative; see [Windows setup](docs/WINDOWS_SETUP.md). **Do not launch on a public host.**

## First real workflow

1. Select **New sandbox**. Use seed `42`, 128 patterns.
2. Run **Forensic Audit** and open its evidence queue. Inspect exact image-copy leaks, group overlap and other flagged patterns.
3. Open a finding and record a review with supporting evidence.
4. Open **Model Failure Explorer**, select **Run baseline**. Then run **Shortcut Inspector** or **Counterfactual Lab**.
5. After reviewing confirmed training samples, run the **Impact Simulator** to compare a removal-only ablation on a frozen test set. An immutable derived dataset version is created.
6. Inspect **Reproducibility**, generate a controlled defect scenario and export JSON, CSV, or printable HTML reports.
7. To test with a genuinely sourced biomedical dataset, download and inspect the original license yourself, then use **Add dataset**. No remote dataset is silently downloaded or redistributed.

## Ten approved enhancements — implemented status

| Enhancement | Delivered behavior | Limitations |
|---|---|---|
| Dataset DNA | Image labels, splits, dimensions, site counts, group coverage, provenance, immutable version lineage | Provenance depends on user-supplied metadata; no automated clinical identity resolution |
| Forensic Evidence Graph | Clickable SVG nodes linking findings and sample records | Capped visualization; no causal or patient-identity inference |
| AI Shortcut Inspector | Frozen model upper-corner mask, flip rate and confidence shift | Controlled perturbation only; not proof of shortcut learning or clinical causality |
| Counterfactual Lab | Actual brightness, blur and corner masking with saved transformed images + predictions | Limited predefined perturbations; no medical-equivalence claim |
| Cross-Dataset Reliability Lab | Frozen model on matching-label, matching-modality secondary dataset; content overlap block | A common label vocabulary does **not** guarantee clinical comparability; lacks real-world external validation |
| Human Review Intelligence | Review outcomes, notes, duration, append-only review history, current disposition | No multiuser identity verification or expert adjudication |
| Audit Impact Simulator | Train model before/after excluding confirmed training images; fixed test ID hash, derived version | Exploratory removal-only ablation; no causal or clinical effectiveness claim |
| Research Reproducibility Engine | Seeded experiments, manifest hashes, environment/software versions, artifact export, scenario ground truth | Platform and dependency changes may affect exact numerical repeatability |
| Model Failure Explorer | Misclassifications, confidence, confusion matrix, site breakdown and metrics with bootstrap CI | Small subgroup metrics may be unstable and must not support fairness conclusions |
| Privacy & Integrity Guard | Local-only API, bounded uploads, path validation, ZIP guard, no remote inference, protected file routes, optional token | Not a certified PHI platform or a replacement for governance, authentication and security review |

Additional functional modules: dataset import (`.npz` MedMNIST-like or ZIP+CSV), SHA-256/pixel hashes, perceptual hash + SSIM candidate retrieval, split/group checks, out-of-fold label suspicion, source-label exploratory statistics, investigation review, IGAT hypothesis ranking vs random/confidence/severity, background jobs, and downloadable audit reports.

## Research-specific strengths and limitations

### Observations vs conclusions

- **Exact content duplicates:** verified by hashes, but content identity alone does not prove patient identity.
- **Perceptual near-duplicates:** thresholded approximate matches to inspect, not guaranteed duplicates.
- **Metadata group overlaps:** only as meaningful as documented group semantics; lesions are not patients.
- **Model-label disagreement:** flags an annotation to investigate, *not* a medically confirmed error.
- **Source-label association:** observational, not evidence of model shortcut causality.
- **IGAT ranking:** experimental fixed heuristic; **not novel or superior until validated** with fair baselines and independent review.
- **Model metrics:** small synthetic benchmarks establish **functionality only**. Real research validation is outstanding.

### Prior research

The motivating methods and adjacent established work include Confident Learning (Northcutt et al., 2021), Cleanlab Datalab, the MedMNIST benchmarks, MedMNIST-C and the 2026 G-AUDIT study. See [research protocol and source links](docs/RESEARCH_PROTOCOL.md). Combining existing data-quality detectors is **not** claimed as a novel research method.

## Import formats

### MedMNIST-compatible `.npz`

`train_images`, `train_labels`, `val_images`, `val_labels`, `test_images`, `test_labels` arrays, all in one archive. Arrays must be 2D grayscale or RGB image collections with single class labels. Upload cap 150 MB. Max samples per split is set explicitly during import, default `2,000`. The resulting manifest records source counts and subset sampling. No pickle is loaded.

### Image ZIP + CSV

Archive layout:

```text
research_images.zip
├── samples.csv
└── images/
    ├── img_001.png
    └── img_002.png
```

` samples.csv ` minimum columns:

```csv
sample_id,image_path,label,split,patient_id,site_id
sample-001,images/img_001.png,class_a,train,group-001,site_alpha
sample-002,images/img_002.png,class_b,test,group-002,site_beta
```

Accepted splits: `train`, `val`, `test`. Optional columns: `patient_id`, `lesion_id`, `group_id`, `site_id`, `source_record_id`. IDs are not automatically interpreted as real patient identity. The ZIP and image safety limits are listed in [data governance](docs/DATA_GOVERNANCE.md).

## Application modules

- `backend/api.py` — REST API and local web server
- `backend/db.py` — SQLAlchemy database model (SQLite default; PostgreSQL configurable)
- `backend/ingest.py` — demo generator, ZIP+CSV and NPZ imports
- `backend/analysis_engine.py` — deterministic detectors, evidence graph, IGAT comparisons
- `backend/labs.py` — CPU research model and evaluation laboratories
- `backend/worker.py` — persistent job dispatcher and cancellation checkpoints
- `backend/security.py` — local file/storage protection
- `frontend/static/` — responsive standalone browser interface (HTML/CSS/JavaScript)
- `tests/` — end-to-end API and computation tests
- `docs/` — research protocol, data governance, UI system and release audit

## Why the UI is not Next.js yet

The earlier specification proposed Next.js. This **runnable release uses a standards-based dependency-free SPA** for the frontend served by FastAPI because the execution environment's npm registry was unreachable. The JSON API and backend layers are separate, so the UI can be migrated to Next.js without rewriting detectors. The choice is documented rather than misrepresented as a Next.js implementation.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

The tests exercise imports, synthetic data, all audit families, review and graph, jobs, a baseline model, shortcut/counterfactual/cross-domain experiments, impact versioning, scenario versioning, reports and path safety. Running tests does not modify your normal `data/` folder.

## Optional PostgreSQL

For local PostgreSQL 18:

```powershell
.\.venv\Scripts\python.exe -m pip install "psycopg[binary]"
$env:DATABASE_URL="postgresql+psycopg://meddata_user:YOUR_PASSWORD@localhost:5432/meddata_forensics"
.\.venv\Scripts\python.exe start.py
```

Create the database/user separately; never put passwords in Git or screenshots. SQLite works without this setup. This research build uses SQLAlchemy's `create_all`; a reviewed Alembic migration workflow is needed before a production upgrade.

## Publication-oriented hypothesis

**Proposed paper:** *Evidence-Guided Prioritization of Data Integrity Risks in Biomedical Image Datasets: Development and Experimental Evaluation of MedData Forensics.*

**Study question:** Can evidence-supported IGAT ranking discover more independently verified, consequential problems within the same human-review budget than random, detector confidence, severity and Cleanlab-derived reference approaches?

The current implementation does **not** establish the answer. Controlled synthetic benchmark generation is in place, but expert labels, external datasets, preregistered thresholds, statistical analysis and validation are necessary. See [research protocol](docs/RESEARCH_PROTOCOL.md).

## No-hardware promise

Every implemented module runs on a normal Windows laptop, using CPU-only Python libraries and locally stored research data. Initial evaluation works with synthetic shapes, and real-data validation requires authorized public datasets, not access to medical equipment.

License for code: MIT. Third-party imported datasets are **not** covered by the code license.
