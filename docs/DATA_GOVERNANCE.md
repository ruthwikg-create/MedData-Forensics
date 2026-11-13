# Data governance, privacy, licensing and integrity

## Intended use

Research and educational quality assessment of properly licensed, appropriately de-identified or synthetic biomedical images. It is **not** a clinical patient-data processing service and should not be used as a substitute for information-security review, local policy or patient consent.

## Storage and protection

- Raw image files are stored under `data/<dataset-id>/images/`, not in the frontend asset directory.
- File delivery goes through a validated database mapping + safe-path check.
- Reports and model artifacts are stored under `artifacts/` with restricted file extension serving.
- Uploaded ZIP content is checked for traversal and symlinks, count and decompressed size caps. Images are decoded with pixel/size checks before analysis.
- `.npz` uses `allow_pickle=False`; array dimensions and split structure are validated.
- Server binds to `127.0.0.1` by default. Optional `MDF_ACCESS_TOKEN` supports session-cookie authentication; **this is not a production identity system**.
- `data/` and `artifacts/` are excluded from Git. Never commit patient information, user credentials, raw third-party datasets or trained weights with ambiguous licenses.
- No telemetry, cloud inference, remote API calls or automatic dataset downloads.

## Limits

- Uploaded NPZ maximum: 256 MiB, including standard PathMNIST-size sources; uploaded ZIP maximum: 150 MiB. These are independent server-enforced caps, not only browser checks.
- ZIP uncompressed size maximum: 900 MB, maximum 12,000 entries, maximum 10,000 CSV rows.
- Image maximum: 20 MB per file and 25 million decoded pixels.
- NPZ import: 2D single-label images with height/width each ≤256, maximum 10,000 samples per split; default subset limit 500.
- Perceptual near-duplicate candidate retrieval is bounded for laptop feasibility; truncation is disclosed in audit metadata.

## Known gaps

This prototype has no formal threat modeling, security penetration test, multiuser authentication, role-based authorization, encrypted per-field PHI storage, HIPAA/DPDP institutional compliance claim, device qualification, or clinical deployment authorization.

Privacy and integrity checks operate on files and metadata but **do not confirm that identifiable information has been removed from images**. If a DICOM or radiology file can include burned-in patient identifiers, do not assume it is safe for this importer.

## Source and licensing

- MedMNIST: https://medmnist.com/v2 — check individual source-specific dataset terms.
- HAM10000: https://doi.org/10.7910/DVN/DBW86T — confirm permitted use and attribution.
- ISIC 2020: https://challenge.isic-archive.com/data/ — check source documentation, attribution and restrictions; do not assume permission for commercialization.
- Cleanlab: optional open-source library — verify current license and version before redistribution.

**The project's MIT license covers newly written code, not independently imported images or metadata.**

## Responsible research

- Preserve raw source data and provenance hashes; create derived versions for experiments.
- Use documented group ID semantics; one lesion ID is not a globally valid patient ID.
- Never silently relabel an image based on a model's prediction.
- Reviewers must preserve uncertainty and rationales; lack of agreement is itself a research observation.
- Do not publish small-group sensitive attributes, identifying photos, or source records if restricted by license or ethics agreements.
