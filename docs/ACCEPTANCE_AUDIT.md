# Final acceptance gate — MedData Forensics v0.9.0 (13 November 2026)

**Scope: software-only research prototype, NOT clinical software.**

The release claims functional verification only for checks actually run. The application cannot be called an independently validated biomedical research method or clinically safe product without additional external evidence.

| # | Acceptance criterion | Status | Measurable evidence and remaining gap |
|---|---|---|---|
| 1 | All modules work on real, properly licensed biomedical data | **PARTIAL — not verified with a real medical dataset in this environment** | NPZ/ZIP ingestion and experimental modules pass constructed-data tests; the official CC BY 4.0 PneumoniaMNIST retrieval+smoke-test script is included. This runtime has no Zenodo access. Real-data execution and domain-specific compatibility/clinical label checks remain necessary. |
| 2 | Every suspected problem links to inspectable evidence | **PASS for tested detector families; clinical interpretation unverified** | Findings have audit ID, detector version, evidence JSON, source sample(s) and a review link. Dedicated API regression test checks evidence. Source/label association findings are global and have structured statistics, not individual-image proof. |
| 3 | Reviewer decisions preserved and reversible | **PASS (local single-user model)** | New decisions append Review rows and update current status; test checks confirmed→rejected→uncertain sequence and history. There is no independently verified reviewer identity or multi-rater adjudication process. |
| 4 | Evaluations use isolated, correctly constructed test sets | **PARTIAL — screened for known leakage** | Evaluation now excludes val/test records overlapping earlier partitions by exact file hash, decoded pixel hash or declared group ID, and records excluded IDs and reasons. No trustworthy patient IDs means patient independence is NOT proven; near duplicates/hidden confounding can remain. Tests confirm an injected cross-split duplicate is excluded. |
| 5 | Existing baselines and IGAT compared fairly | **PARTIAL — synthetic proof-of-operation only** | All methods rank the same candidate set at the same review budget; random ranking now averages 30 fixed-seed trials. IGAT, severity and confidence are compared on known injected synthetic defects. Independent expert labels, Cleanlab baseline on natural data, blind review and preregistration are outstanding. |
| 6 | Uncertainty estimates and failure analysis included | **PASS on synthetic local runs; external statistics pending** | Cluster-resampled bootstrap macro-F1 and accuracy intervals when declared groups are available, plus calibration, per-class confusion matrix and subgroup counts. Paired cluster-bootstrap macro-F1 difference added to impact experiments. Small sample/unknown group limitations are disclosed. |
| 7 | Windows install without Docker or GPU | **CODE REVIEWED, WINDOWS DEVICE EXECUTION PENDING** | `RUN_ME_WINDOWS.bat`, `Setup-Windows.ps1`, `Start-Windows.ps1`, `Test-Windows.ps1`, no Docker/CUDA and pure CPU model. Linux-hosted tests run. This environment cannot execute PowerShell on Windows. |
| 8 | End-to-end, security, and integrity checks pass | **PARTIAL — automated local checks passed, full security review pending** | Python backend / API integration tests, Node frontend tests, upload traversal, tamper detection, token access, status-history, synthetic scenario / experiment tests pass locally. No external penetration test, adversarial robustness audit, real-world concurrency, or broad browser/device matrix testing. |
| 9 | Exported records permit reproducibility and disclose limitations | **PARTIAL — metadata bundle implemented** | JSON reproducibility export includes record hashes, dataset manifest, audit configs, evidence, reviews and experiment manifests. On-demand verifier detects file tampering. Original authorized image data, model binaries, exact runtime, and upstream provenance still needed for independent reexecution. |
| 10 | Repo documentation and no fabricated clinical claims | **PASS for inspected local source** | README, governance, protocol, manuscript draft, explicit research-only labeling, acceptance matrix, test instructions. GitHub replication and CI must be separately checked after publishing this revision. |

## How to verify software features locally

Windows PowerShell from the cloned repository:

```powershell
.\RUN_ME_WINDOWS.bat
# In another PowerShell window, from the project root:
.\scripts\Test-Windows.ps1
```

The UI Reproducibility Engine can now **Verify dataset hashes** and export **Reproducibility + file integrity bundle** (or call `/api/datasets/{id}/verify` and `/api/datasets/{id}/report?format=repro`).

For the **official licensed-data smoke test**, stop unrelated heavy workloads and execute:

```powershell
.\scripts\Run-RealDataset-Sanity.ps1
```

It downloads from the official MedMNIST Zenodo record, verifies the published MD5, and evaluates a bounded sample. It stores the dataset privately under `data/`; DO NOT upload the dataset to GitHub. Results remain research-only and must be reviewed for split and subgroup validity.

## What would move the project to research-validated status?

1. Complete official dataset ingestion and reproducibility on a Windows machine, document data license and source publication, and verify hashes.
2. Build independently adjudicated natural-data issue ground truth, blinded to IGAT ranking, with disagreement analysis.
3. Complete matched Cleanlab and conventional-detector baselines, predefined review budgets and subgroup-aware statistics, and report negative results.
4. Evaluate with at least one additional appropriately licensed biomedical image dataset and disclose how its labels and grouping differ.
5. Obtain a scoped security assessment and exercise install, updates and recovery on a clean Windows 11 system.

**Do not represent the current prototype as approved for clinical care, as a certified device, or as publication-ready efficacy evidence.**
