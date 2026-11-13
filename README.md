# MedData Forensics

<p align="center">
  <img src="assets/meddata-forensics-logo-white.svg" alt="MedData Forensics wordmark on a white background" width="460">
</p>

**Local-first biomedical AI dataset investigation and reproducibility workbench.**

> **RESEARCH ONLY.** This software does not diagnose patients, establish image-label truth, certify a medical device, validate a model for clinical use, or establish a dataset's clinical suitability. All new/demo test results refer only to synthetic geometric phantoms unless a dataset is explicitly identified as an independently sourced research dataset. No real-world model validation or accepted research-paper contribution is claimed.

**Current release: v0.9.2 interactive research labs and import feedback.**

MedData Forensics imports image classification datasets, identifies potential data-integrity risks with inspectable evidence, lets researchers review findings, and runs CPU-friendly comparative experiments. Every original dataset remains unchanged. No medical equipment, CUDA GPU, Docker or paid API required.

## About the Creator

**Goparaju Ruthwik** is a Biomedical Engineering student at the **University College of Engineering, Osmania University, Hyderabad**, with interests in **AI/ML for healthcare, medical imaging, biomedical research, and healthcare software development**.

I build research-oriented software that helps make biomedical data more trustworthy and AI experiments easier to inspect. With MedData Forensics, my goal is to help researchers explore dataset integrity, potential leakage, model failure patterns, and reproducible evidence without claiming clinical validation where it has not been established.

**GitHub:** [@ruthwikg-create](https://github.com/ruthwikg-create)




## Reliability repairs — November 13, 2026

The current `main` branch includes additional tested reliability patches after v0.9.2:

- **Baseline readiness:** Model Failure Explorer now reports train/test counts, observed class support, reasons that training cannot start, low-support cautions, and the latest baseline job error. A completed database record without its `baseline.joblib` file does not unlock dependent experiments.
- **Sorted, imbalanced NPZ datasets:** subset import now chooses a deterministic, class-preserving selection instead of blindly importing the first N records. Source array indices and source/selected class counts are recorded. Sampling changes class prevalence and is not equivalent to full-dataset evaluation.
- **Rare-class smoke tests:** the CPU classifier can fit when a class has only one or two training examples, but the result prominently warns about severe uncertainty. At least 20 training records, two classes, and independent test records are still required.
- **Shortcuts and external comparisons:** shortcut sensitivity uses the baseline's leakage-screened test cohort. Cross-dataset experiments block both identical file bytes and pixel-identical re-encodings.
- **Evidence graph:** readable interactive node cards replace compressed line-only visualizations, with explicit labels for unlinked records.
- **Regression tests:** separate Linux research and Windows software-acceptance workflows passed on these patches. This does not prove reliability on a particular user's computer or establish clinical validity.

**If you imported an NPZ before the class-preserving sampling fix, re-import it as a new dataset** to apply the new selection. The previous dataset remains unchanged. After cloning from GitHub, stop the old server, run `git pull origin main`, restart `RUN_ME_WINDOWS.bat`, and force-refresh the browser (`Ctrl+Shift+R`). ZIP-extracted folders are not Git clones and cannot receive `git pull` updates.

### Reproduction checklist

1. Create a new synthetic sandbox (seed 42, count 128).
2. Select **Forensic Audit**, run the audit, and confirm its job completed before opening Evidence Graph and Compare.
3. Open **Model Failure Explorer**, read **Baseline readiness**, then run baseline training; check the exact error if it fails.
4. Run Shortcut Inspector or Counterfactual Lab only after the baseline checkpoint is present.
5. Cross-Dataset Lab needs a separate, compatible collection without image overlap. Impact Simulator needs confirmed training-sample findings.
6. Run `powershell -ExecutionPolicy Bypass -File .\scripts\Test-Windows.ps1` from the project root to test your own Python environment. This command uses the local virtual environment; no GPU, Docker, or paid API is required.


## What changed in v0.9.2

- **Import:** real transfer percentage is shown while the `.npz`/`.zip` file uploads; decoding and indexing display an explicitly indeterminate state, followed by a persistent success or error message. This does not provide a fictitious CPU indexing percentage.
- **Experimental Review Ranking:** the Compare control changes the review budget and displays the top ranked **actual finding records** for IGAT, confidence, severity and the seeded random baseline. On externally sourced research data without independent defect truth, the software compares **review order only**, not detection precision. Synthetic planted defects can be scored separately.
- **Evidence Graph:** real, selectable image and finding nodes, with a finding index and clearly labelled sample-only inventory before the first audit. No unsupported edges are generated. Run a forensic audit first to obtain evidence connections.
- **Shortcut Inspector:** train the baseline in Model Failure Explorer first. The app now exposes this prerequisite instead of starting an experiment guaranteed to fail. The real probe uses a frozen model on imported test images and reports sensitivity, not causal proof of a shortcut.
- **Counterfactual Lab:** image selector, real local image preview, brightness/blur/corner mask visual controls, and an experiment strength slider. The CPU experiment applies four recorded, controlled transforms to the selected image and preserves the strength in the result. **A visual preview is not a model output.**
- **Privacy and Integrity:** the access-token panel now explains whether `MDF_ACCESS_TOKEN` is actually enabled. By default no token is needed on loopback. Never expose the workstation as a public service.

For a step-by-step workflow and interpretation limits, see [Lab troubleshooting](docs/LAB_TROUBLESHOOTING.md).

## Distinct research workspaces without a dataset

All ten research modules now display a **different, clearly labeled instructional workspace** before data is imported. Dataset DNA previews lineage structure; Forensic Audit explains its detector pipeline; Evidence Graph shows a conceptual network; Review Center explains its four decision states; Shortcut Inspector shows a synthetic region mask; Counterfactual Lab offers working synthetic brightness, blur and masking previews; Cross-Dataset Lab explains compatibility; Impact Simulator shows the frozen-test evaluation design; Model Failure Explorer explains the confusion matrix; and Reproducibility shows an illustrative experiment manifest. None of these previews are real audit findings or model predictions.

Use **Create synthetic dataset** or **Import real research data** in any module to unlock actual dataset-backed analysis. Each module remains distinct after loading, with its own real results. See [Workspace guide](docs/WORKSPACE_GUIDE.md).

**After updating from GitHub:** stop the running server, execute `git pull origin main` in your cloned repository, restart `RUN_ME_WINDOWS.bat`, and force-refresh Chrome with `Ctrl+Shift+R`. The application is not updated by pulling from a ZIP-extracted folder.

## Dataset import feedback (v0.9.1)

The **Add dataset** dialog now shows the real uploaded-byte percentage, followed by an indeterminate **Validating and indexing** phase. No invented indexing percentage or completion time is shown; large image imports may take time on CPU. On successful server confirmation, the dialog shows **Dataset imported successfully** and a **View Dataset DNA** action. The app updates its active dataset and retains the success message until you open the workspace. Failures remain visible with the returned validation error and a retry button. Repeat uploads are blocked while processing, and the dialog cannot be dismissed accidentally during an active import.

**Important:** The local API currently handles dataset indexing synchronously. Its browser progress meter measures file transfer only; after transfer completes, the phase indicator remains active until the API responds. Separate compressed-package limits apply: NPZ up to 256 MiB (including the standard PathMNIST NPZ), ZIP up to 150 MiB. The server keeps the existing 900 MiB NPZ expanded-data guard, array validation, and split sampling. Choose a small NPZ subset (500 images per split by default) when using a CPU laptop. Split sampling happens after upload and cannot shrink the source file. Do not assume the import succeeded until the success state appears in the modal and the dataset is visible in Dataset DNA.

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

`train_images`, `train_labels`, `val_images`, `val_labels`, `test_images`, `test_labels` arrays, all in one archive. Arrays must be 2D grayscale or RGB image collections with single class labels. Upload cap 256 MiB for `.npz` (ZIP remains 150 MiB). Max samples per split is set explicitly during import, default `500`. The resulting manifest records source counts and subset sampling. No pickle is loaded.

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


## Navigation and empty datasets

All research sections can be opened before a dataset is imported. Each page explains its own purpose and the steps required to use it. No dataset-specific results are shown until data is loaded; this is expected behavior. In particular, **Counterfactual Lab**, **Shortcut Inspector**, **Cross-Dataset Lab** and **Impact Simulator** must not silently display the Overview page when the dataset list is empty.

To begin, choose **New sandbox** (safe synthetic images) or **Add dataset** (an authorized research dataset). The application returns you to the section you were using after creating a sandbox. For model-based labs, train the CPU baseline first in **Model Failure Explorer**.

The frontend routing regression suite runs without installing JavaScript packages:

```powershell
node --test tests/test_frontend_routes.cjs
```

## Acceptance gate: verification added in v0.9.0

The ten final acceptance criteria are tracked explicitly in [docs/ACCEPTANCE_AUDIT.md](docs/ACCEPTANCE_AUDIT.md). Passing software tests does **not** establish real biomedical model validity.

- **Data integrity:** `GET /api/datasets/{dataset_id}/verify` re-hashes local images and verifies stored dataset manifest. Available as a button in the Reproducibility Engine.
- **Reproducibility export:** Download `GET /api/datasets/{dataset_id}/report?format=repro` to obtain sample hashes, audit configurations, evidence, reviews and experiment manifests. This metadata bundle excludes raw images and model binaries.
- **Leakage safeguards:** baseline and impact evaluations screen test/validation partitions against earlier splits using available group IDs, file hashes and decoded-pixel hashes. Records removed from evaluation are explicitly listed. Missing patient IDs cannot be corrected automatically.
- **Uncertainty:** subgroup-cluster bootstrap summaries and paired impact delta intervals are included. Small samples or missing grouping constrain interpretation.
- **IGAT ranking:** equal-budget heuristic comparison plus 30 seeded random-baseline trials on known synthetic defects. No claim of superiority or real-world generalizability.
- **Real-data verification:** `scripts/Run-RealDataset-Sanity.ps1` fetches official CC BY 4.0 PneumoniaMNIST (28x28) from MedMNIST's sole official distribution Zenodo, verifies MD5, and runs a CPU smoke test. It has **not** been run in the assistant's internet-restricted environment. Data is never bundled with this repository.

### Windows acceptance tests

```powershell
.\scripts\Test-Windows.ps1
```

The Windows script checks Python backend tests and, when Node.js is installed, frontend routing tests. For a real-data smoke test use `scripts/Run-RealDataset-Sanity.ps1` after reviewing the data license. Do not treat successfully opening the app as proof that all research validation criteria are met.

### Clear analysis notifications

Open the **bell** in the top-right corner to view **Notifications & analysis jobs**. Choose **Clear** beside a completed, failed, or cancelled job, or **Clear notifications** to dismiss all finished-job notices at once. Active/running jobs cannot be dismissed and remain visible. Clearing affects notification visibility in the current browser (stored in local storage); it **does not delete** job records, failed-job error messages, audit findings, experiments, or datasets. Use **Show recent history** in the bell dialog to inspect cleared job messages (the API returns the latest 35 jobs). The bell indicator includes active jobs and uncleared finished jobs.
