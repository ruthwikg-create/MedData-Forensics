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

## Debugging failed experiments

Open **Analysis Jobs** (bell icon). Look for the latest job status and error reason. A failed baseline can result from a missing test split, too few independent test records after identity-screening, or insufficient class representation. A successful HTTP request to queue an experiment is not equivalent to a completed experiment.

Tests: `python -m pytest -q` and `node --test tests/test_frontend_routes.cjs tests/test_import_progress.cjs`. This release has been verified with a synthetic dataset in an end-to-end API workflow and browser-rendering checks using controlled local responses; independently verified clinical research results remain pending.
