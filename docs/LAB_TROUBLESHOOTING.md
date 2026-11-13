# Interactive research labs: use and limitations

All application experiments are software-only and research-only. They do not certify a diagnostic system, establish medical label truth or replace expert adjudication.

## Start with a valid dataset

1. Open the local app with `RUN_ME_WINDOWS.bat`. In **Add dataset**, choose an authorized `.npz` (MedMNIST) or small `.zip` containing `samples.csv`. Start with 500 images per split on CPU.
2. Upload progress is based on bytes transferred to localhost. The **indexing stage is indeterminate** because the server does not send per-image processing updates. The successful import result appears only after an API response confirms indexing is finished.
3. Visit **Dataset DNA** to check train/validation/test counts, known group IDs and provenance.

## Ranking Compare

1. Open **Forensic Audit**, choose **Run audit**, then open **Analysis Jobs** to confirm it completed.
2. Under **Experimental review ranking**, choose the review budget and press **Compare**.
3. Open any listed candidate to inspect evidence. On genuine research image datasets lacking independently adjudicated defect truth, *rank-order agreement* is shown; precision / confirmed defect counts cannot be claimed. Planted-defect sandbox datasets have a separate synthetic reference.

## Evidence network

1. Select your dataset and run a completed forensic audit.
2. Open **Evidence Graph**. Click an image-record node or finding node to view the underlying record or forensic evidence.
3. If no audit exists, the graph shows isolated actual sample nodes with **zero invented links** and invites you to run one. After an audit with no linked findings it still does not fabricate connections.

## AI Shortcut Inspector

1. Go to **Model Failure Explorer** and run **Train baseline**. This creates a small CPU classifier checkpoint. A queued or failed baseline is not ready.
2. After the job is marked **completed** in Analysis Jobs, open **Shortcut Inspector** and press **Probe shortcut sensitivity**.
3. Inspect prediction flip rate and confidence changes under controlled corner occlusion. A strong response is not proof of confounding or shortcut causality, especially with 28×28 image input.

## Counterfactual Lab

1. Complete the baseline checkpoint.
2. Select a sample and a visual preview transformation (brightness, blur, mask); adjust strength. This browser preview is not the classifier prediction.
3. Press **Run image perturbations**. The worker applies four standardized transformation families at the *recorded strength*. Completed results provide transformed images, predicted classes, probabilities and changed-prediction flags. Each run is linked to its selected sample ID; switching samples requires a new run to compare that sample.
4. Download experiment manifests from **Reproducibility**; record the source dataset and its license.

## Access token

`MDF_ACCESS_TOKEN` is **optional**. If not set, the local server on `127.0.0.1` does not need a password and the token field can be left empty. If you explicitly set `MDF_ACCESS_TOKEN` in PowerShell **before launching the app**, enter that exact secret in **Privacy & Integrity** so the browser can access protected API routes. The token is stored in session storage for the current browser tab. Do **not** paste the token into GitHub, screenshots, or chat. Do not use the loopback prototype for identifiable patient data or as a publicly exposed server.

## Repairing repeated baseline and graph failures

Use the **Baseline readiness** section in Model Failure Explorer before starting a new run. It displays train/test counts, per-class training support, prerequisite failures, warnings, and the error from the latest baseline job. If an older model record says "completed" but its saved checkpoint was deleted, retrain: downstream labs require the real file.

Previously imported class-sorted NPZ subsets do not change in place. Re-import the original authorized NPZ to use deterministic class-preserving sampling; inspect the dataset's sampling manifest and label distribution. Low-support classes are supported for software smoke tests but **not** for reliability or biomedical-model validity claims.

Graph connections require a completed forensic audit and at least one detector-supported image/finding link. Isolated dataset records are not a broken connection and must not be drawn as invented edges. Ranking Compare similarly requires actual audited findings.

A shortcut-sensitivity result uses the baseline's leakage-screened held-out test records. Cross-dataset experiments reject exact file duplicates and re-encoded pixel-identical content; neither screen alone establishes patient independence.



## Using the four research workspaces

**Import modality matters:** Choose the real acquisition type when importing a dataset. `Biomedical 2D image` and `Other / unspecified` are deliberately not accepted as evidence of modality compatibility. For example, choose `Dermatoscopic / skin lesion images` for HAM10000 and DermaMNIST, and `Histopathology / microscopy` for PathMNIST. Re-import older collections whose modality is generic; do not relabel a dataset merely to bypass a compatibility check. **Important lineage restriction:** DermaMNIST is derived from HAM10000 and contains resized images from that source, so they must not be presented as independent external datasets for Cross-Dataset Lab. PathMNIST is histopathology and is not a modality-compatible target for HAM10000. Use the synthetic pair only to test the UI, or obtain a genuinely independent dermatoscopic collection with documented matching classes for a real external evaluation.


- **Cross-Dataset Lab:** select a source dataset, train its baseline, and import a second independent dataset. Exact class names can be used directly. If class names differ but the class counts match, the mapping panel requires a documented one-to-one mapping and an explicit researcher confirmation. Modality mismatch, missing target test split, exact hashes or decoded-pixel duplicates still block the comparison. Use **Create two synthetic collections to test this lab** only to verify the software workflow; those collections are not biomedical data.
- **Impact Simulator:** run a completed audit, open Review Center, inspect a supported finding linked to a training image, and record a reasoned confirmation only when the evidence warrants it. If no eligible issue exists, the experiment correctly remains unavailable. The **Create synthetic test dataset** action creates a separate sandbox with planted software-test defects; review its findings manually rather than auto-confirming them.
- **Failure Explorer:** check the Baseline readiness panel first. If it reports blockers, fix the split, sample-count or class-support issue before training. A completed experiment record without its saved checkpoint is not enough; retrain if the panel says the checkpoint is missing.
- **Reproducibility:** select a dataset, then use **Download reproducibility bundle** or **Verify file hashes** immediately. Previous experiments are not required. The experiment registry fills as completed, active and failed runs are recorded. The bundle contains metadata and evidence, not original images or model binaries.


## Debugging failed experiments

Open **Analysis Jobs** (bell icon). Look for the latest job status and error reason. A failed baseline can result from a missing test split, too few independent test records after identity-screening, or insufficient class representation. A successful HTTP request to queue an experiment is not equivalent to a completed experiment.

Tests: `python -m pytest -q` and `node --test tests/test_frontend_routes.cjs tests/test_import_progress.cjs tests/test_notifications.cjs`. This release has been verified with a synthetic dataset in an end-to-end API workflow and browser-rendering checks using controlled local responses; independently verified clinical research results remain pending.


## Clear analysis notifications

In **Analysis Jobs** (bell icon), use **Clear** on a finished job or **Clear notifications** to hide all completed, failed and cancelled notices from the current browser. Active queued/running jobs always remain visible and can still be cancelled. Use **Show recent history** to review cleared messages and failed-job error reasons. Clearing does not remove persisted jobs, audits, model artifacts, research results, or datasets.


## Multiclass baseline failure and Evidence Graph

Model Baseline and audit label-quality analysis use scikit-learn logistic regression with a multinomial-capable `lbfgs` solver, so authorized research datasets with **three or more classes** (for example PathMNIST) no longer fail solely because the old `liblinear` solver rejected multiclass fitting. Training still requires sufficient observations in multiple classes and a leakage-screened held-out test partition. Other dataset or environment failures remain possible and are reported in **Analysis Jobs**. Old failed jobs are not rewritten; run a **new** baseline after updating.

The Evidence Graph is **detector-evidence-only**. It never draws fabricated links to make the display look full. After a completed audit with only dataset-wide findings or no linked findings, the graph shows **real isolated image-record nodes** plus any global finding nodes, with an explicit no-links explanation. When findings have image identifiers, the network draws and labels those edges. Open **Forensic Audit** first, check Analysis Jobs for completion, then open **Evidence Graph** and click **Reload graph**.


## Cross-Dataset Lab: no target collection is available

Cross-Dataset Lab needs **two separately imported collections**. Selecting HAM10000 as the source does not automatically create a second collection. If only one dataset is loaded, use **Import another dataset** in the lab. If other datasets are present, the compatibility panel explains why each is unavailable.

A selectable target must have:
- the same declared image modality as the source;
- exactly the same label strings as the source model's training classes;
- a held-out `test` partition;
- no known exact-file or recorded decoded-pixel hash overlap.

The worker performs an additional decoded-pixel identity check. Do not relabel classes or choose a different modality merely to bypass this gate. Matching names and modality do not prove clinical equivalence. If your authorized second dataset uses numeric MedMNIST class IDs while HAM10000 uses diagnosis strings, Cross-Dataset Lab now offers an explicit one-to-one mapping panel when the class counts match and the other compatibility checks pass. Map every target label to a distinct source class and confirm that the mapping is supported by the original dataset documentation. The application never guesses what a numeric class means. For example, do not compare PathMNIST histopathology with HAM10000 dermatoscopic images merely because the class counts happen to match.

## Impact Simulator: no confirmed training-image findings

The Impact Simulator is a **removal-only ablation**, not a general baseline comparison. It requires a completed forensic audit and at least one reviewer-confirmed finding that links to an image in the `train` split. Eligible finding families are split leakage, group overlap, exact/pixel/near duplicates and label suspicion.

1. Run **Forensic Audit** and wait for the job to complete.
2. Open **Review Center** and inspect the actual evidence and linked image records.
3. Confirm a finding only when its evidence supports the concern. A dataset-wide finding, a source-association-only finding, or a finding linked only to validation/test images does not qualify.
4. Return to **Impact Simulator**. Its readiness panel reports the count of confirmed training records eligible for removal and whether the CPU model-fit subset still contains enough examples/classes.
5. Run the removal-only ablation only when the panel says **Ready to run**.

If the audit finds no eligible concerns, the correct outcome is that the Impact Simulator remains unavailable. Do not manufacture confirmations to force an experiment. Original image files and labels are not overwritten; the experiment creates a separate derived metadata version and retains the fixed held-out test cohort.
