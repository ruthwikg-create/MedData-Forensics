# Historical v0.8.0 release snapshot

For the **current v0.9.0 acceptance assessment**, see [ACCEPTANCE_AUDIT.md](ACCEPTANCE_AUDIT.md). The historical checks below should not be interpreted as current research validation.

# Release acceptance audit — 0.8.0 research build

## Functional verification

| Requirement | Verified status | Evidence |
|---|---|---|
| Python app imports/launches | Passed locally | `python -m compileall` and `/api/health` |
| Image ZIP + CSV import | Passed local automated test | `tests/test_research_workflow.py` |
| MedMNIST-style NPZ import | Passed local synthetic NPZ test | `tests/test_research_workflow.py` |
| Synthetic demo with controlled defects | Passed local automated test | Seed 42 generation test |
| Audit evidence / group overlap / label suspicion | Passed on synthetic data | Worker + API test |
| Evidence graph and reviewer history | Passed API tests and mocked browser navigation | Graph nodes, review event log |
| CPU baseline, shortcut probe and counterfactuals | Passed local synthetic tests | Worker experiment output assertions |
| Cross-dataset evaluation and overlap safeguard | Passed synthetic independent-seed test | Group/label constraints and hash check in code |
| Reviewer-confirmed impact ablation and derived version | Passed synthetic workflow test | Fixed held-out test hash and child dataset version |
| Scenario generation and report export | Passed synthetic workflow test | JSON/CSV/HTML artifact response |
| Browser navigation / responsive visual mock | Reviewed in headless Chromium with mocked backend responses | Screenshots created in build environment |
| Real third-party biomedical dataset experiments | **Not performed** | No source dataset was downloaded in build environment |
| Clinical/expert label validation | **Not performed** | Requires appropriately qualified independent review |
| IGAT superiority vs baselines | **Not established** | Synthetic controlled outputs are sanity checks only |
| Medical-device / clinical regulatory clearance | **Not obtained** | Research prototype, not a clinical device |
| Windows user-machine installation | **Not verified on user's Windows laptop** | PowerShell scripts supplied; Linux-side tests do not prove local Windows execution |
| Next.js frontend | **Not implemented** | Working dependency-free HTML/CSS/JS SPA instead |
| External security audit | **Not performed** | Local-first guards do not equal production compliance |

## Notable design constraints

- Detector pair generation is **approximate and bounded**, with run metadata describing threshold caps.
- Forensic confidence is not calibrated clinical certainty.
- `MDF_ACCESS_TOKEN` is a single-workstation token, not multiuser authentication.
- Jobs are persisted in SQLite/PostgreSQL; a single local worker handles tasks and checks for cancellation at progress checkpoints.
- Audit study methods and ranking weights are preliminary until preregistered and independently validated.
- AI Shortcut Inspector uses corner masks; it is an observational sensitivity probe, not causal shortcut identification.
- No clinical AI model is trained or claimed from synthetic phantom labels.

## Next release gates before publication

1. Source each biomedical dataset with license, provenance and ethical-use verification.
2. Freeze a research protocol and real-data split policies before experiments.
3. Establish independent reference standards and blinded review.
4. Run Cleanlab/quality detector baselines and IGAT ablations fairly.
5. Run image- and patient/lesion-group-aware confidence interval analysis as applicable.
6. Independently test source/target compatibility and no cross-source overlap.
7. Report failures, false positives, null results, uncertainty, and generalization limitations.

A research paper must be based on actual validated results; **this package is a functioning research prototype, not a completed publication study**.
