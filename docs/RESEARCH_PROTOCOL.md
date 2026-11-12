# MedData Forensics — Research protocol and publication roadmap

**Version:** 0.8.0, 12 November 2026  
**Status:** Preregisterable **proposal**, not completed biomedical research or a submitted paper.

## Working title

*Evidence-Guided Prioritization of Data Integrity Risks in Biomedical Image Datasets: Development and Experimental Evaluation of MedData Forensics.*

## Research question

Does an evidence-supported, cost-aware prioritization method identify more **independently verified, impactful** biomedical image dataset issues under a fixed human-review budget than basic prioritization methods?

## Primary hypothesis and assumptions

- **H1:** The proposed Impact-Guided Audit Triage (IGAT) strategy increases issue yield at a fixed review budget relative to random ranking and score-only strategies.
- **H2:** Issue ranking improves detection of defects that demonstrably alter an untouched evaluation metric. This hypothesis is **not** established by review yield alone.
- **Null:** IGAT provides no improvement or performs worse than baselines. Report negative findings without selectively changing the protocol.
- The current **coded IGAT** is a fixed heuristic: `0.45*detector_confidence + 0.38*severity_score + 0.17*sample_evidence_degree - 0.10*review_cost_scaled`. These weights are **arbitrary research starting points**, not optimized or proven; they must be tuned only on development data if tuning is undertaken. Detector confidence is not calibrated clinical probability.
- The source-label association test and corner masking are **exploratory** and cannot establish causality or demographic fairness.

## Established prior research: required comparisons

1. Northcutt, Jiang, Chuang (2021), *Confident Learning: Estimating Uncertainty in Dataset Labels.* https://research.google/pubs/confident-learning-estimating-uncertainty-in-dataset-labels/
2. Cleanlab Datalab and its label-quality, outlier, and near-duplicate methods: https://docs.cleanlab.ai/stable/tutorials/datalab/datalab_quickstart.html
3. MedMNIST: https://medmnist.com/v2
4. MedMNIST-C corruption robustness benchmark: https://arxiv.org/abs/2406.17536
5. G-AUDIT, 2026, medical dataset bias/shortcut analysis: https://www.nature.com/articles/s41746-026-02807-y
6. CLAIM 2024 medical imaging AI reporting: https://pubs.rsna.org/page/ai/claim
7. Public medical-imaging dataset provenance/leakage research: https://pubmed.ncbi.nlm.nih.gov/42977830/

**Novelty caution:** Similar systems may exist beyond these references. Before a novelty claim, perform a fresh systematic targeted search in PubMed, IEEE Xplore, Scopus and arXiv, document exact query strings and dates, compare implementations in a published related-work table, and evaluate a meaningful unresolved gap. A dashboard combining known checks is not automatically publishable.

## Datasets and splits

### Implementation smoke tests (present)

- Locally generated **synthetic geometric patterns** with controlled labels, random noise, site-color markers, class-shape patterns, planted duplicate pairs, near-copy, group overlaps and training-label flips.
- Synthetic `truth.json` is used only for synthetic test assertions and demonstration ranking. These are **not** medical images.
- A generated scenario copies metadata into a new dataset version and injects seeded training-label flips; original images and labels remain unchanged.

### Research experiments (not yet run or validated)

- DermaMNIST: inspect source terms and official splits. Small 28px variants are suitable for initial CPU tasks, but make no patient-level split claims without actual patient metadata.
- HAM10000: check licensing and lesion grouping. **Lesion identifiers are not verified patient identifiers.**
- ISIC 2020: examine official duplicate list, patient/lesion metadata and source terms; full imaging archive may exceed practical local constraints. Use permissible subsets and document selection.
- PathMNIST: second-modality replication when labels and sampling are documented.
- *Cross-dataset inference only when label and task mappings are clinically defensible.* Matching strings alone is insufficient.

## Experimental design

### Study A — detection quality

1. Define corruption types: exact duplicate, pixel-identical re-encoding, train-test leakage, metadata group split overlap, label corruption, near-duplicate/transform.
2. Generate multiple synthetic scenarios using prespecified seeds and severity levels (e.g., 5%, 10%, 15% injected label error).
3. Compare detector families: SHA-256, pixel hash, perceptual-hash+SSIM, training-only out-of-fold label confidence, optional Cleanlab. Record thresholds and retrieval caps.
4. Metrics: per-type precision, recall, F1, discovery latency, memory and wall-clock cost, false-positive examples. Report pairwise-duplicate matching carefully (not per-image labels).
5. For natural biomedical images, obtain adjudicated sample ground truth; synthetic truth cannot substitute for expert review.

### Study B — IGAT review prioritization

1. Freeze a candidate set and reviewer instructions.
2. Compare **random (multiple seeds), detector confidence, fixed severity, Cleanlab-derived label rank where applicable, and IGAT**.
3. Evaluate predeclared budgets (e.g., 10, 25, 50, 100 reviews) with a consistent cost model.
4. Primary metric: verified distinct consequential issues per unit of reviewer time. Secondary: issue yield at k, precision@k, time-to-first-consequential-finding, duplicates/redundant reviews.
5. Have independent expert raters, where accessible, score cases blind to ranking strategy; calculate inter-rater agreement and a documented adjudication protocol.
6. No tuning on held-out test examples, study outcomes or final adjudicated labels.
7. Compute confidence intervals (bootstrap over independent patients/groups/datasets) and paired tests for strategy comparisons. Explicitly state dependence assumptions.
8. Repeat across at least two differently sourced real biomedical research datasets where licensing and annotation permit; if unavailable, clearly limit conclusions to synthetic data.

### Study C — downstream model impact

1. Train a fixed baseline on official training data only; use validation for model selection.
2. Freeze source/test identifiers and hash them before review and remediation.
3. Apply only **documented, reviewed, bounded** modifications to training data. Preserve a derived dataset version; do not overwrite labels automatically.
4. Retrain the identical model recipe with the same fixed seed and compute paired performance on the same untouched test cohort.
5. Report macro-F1, balanced accuracy, AUROC if appropriate, multiclass Brier score, calibration, confidence intervals, per-class/subgroup outcomes (with support), and potential harms.
6. Report uncertainty, model sensitivity and cases where removal decreases performance. If leakage contaminated an original official test, present a clearly separate preplanned leakage-safe evaluation as a distinct experiment and do not compare to the contaminated score as if both were independent external tests.

### Study D — shortlist stress tests (optional)

- Controlled brightness, blur and marker/corner masking at appropriate ranges.
- Cross-source image evaluation using **frozen models** and documented task/label mappings.
- Confirm that changes are distinguishable from removing true clinical content; if not, results remain exploratory.

## Bias controls and anti-leakage constraints

- Grouped partitions whenever verified patient identifiers exist; use lesion groups only for lesion-level constraints and label them correctly.
- Never derive training-sample label suspicion using test labels.
- Never use final test performance to optimize IGAT weights or candidate selection.
- Detect content overlap between source and target before describing a study as external.
- Use dataset- or patient-level bootstrap units where appropriate, not image-level independence assumptions when correlations exist.
- Match algorithms on identical candidate sets and review budgets; random baseline across 30 fixed seeds on synthetic known defects; real-data independent labels pending.
- Define the review cost and what constitutes a *distinct consequential issue* **before** experiments.
- Keep synthetic ground-truth injections out of any claims about spontaneous clinical annotation errors.

## Implementation baseline details (current code)

- Integrity: image signature and size validation, missing/unreadable files, duplicate sample IDs, raw SHA-256, decoded RGB pixel hashes.
- Near duplicates: 64-bit pHash from DCT, 8-block locality-sensitive candidate retrieval, Hamming ≤7 and 96px SSIM ≥0.935, with candidate caps. Thresholds are illustrative; **not calibrated for biomedical datasets.**
- Training-only label suspicion: cross-fitted logistic regression using HOG and 12×12 RGB pixel features; where present, group-aware folds. Cleanlab score integration is optional if installed; ordinary self-label probability is fallback.
- Source-label association: prespecified chi-square test with Cramér's V when data meets minimal conditions; exploratory, not proof of shortcuts.
- Model: LogisticRegression with `class_weight='balanced'`, fixed seed 42, CPU, held-out test evaluation, 300 group-cluster bootstrap replicates where group IDs exist, with a hash-based fallback when absent; patient-level independence remains unproven without patient metadata.
- IGAT demonstration ranks by fixed evidence, severity, sample connection frequency and review-cost scores; real impact estimates and weights still need validation.
- Impact simulation: remove reviewer-confirmed training rows only, hold the test cohort fixed, compare trained models and preserve a child dataset version.
- Cross-dataset lab rejects identical image hashes, declared modality mismatch and distinct class vocabulary, **but a full clinical mapping/adjudication remains an external research prerequisite**.

## Reproducibility checklist

- [x] Fixed seed included in jobs and experiment manifests.
- [x] Dataset version fingerprint and source identity recorded.
- [x] Python / NumPy / SciPy / scikit-learn platform versions in manifests.
- [x] Code revision recorded when project is in Git.
- [x] Human-review history kept independently of source files.
- [x] JSON, CSV, HTML report export.
- [x] Tests for controlled synthetic workflows.
- [ ] Third-party dataset license and annotation provenance verified for selected study.
- [ ] Independent medical expert review labels and inter-rater reliability.
- [ ] A preregistered prospective ranking protocol and search for prior methods.
- [ ] Real biomedical dataset replication and external validation.
- [ ] Robustness across class/task group sizes, image resolution and noise.
- [ ] Independent subgroup/cluster-aware confidence intervals and statistics.
- [ ] Submission-ready paper with genuine experimental findings.

## Proposed paper sections

1. Introduction and clinical/research motivation
2. Related work and precise novelty position
3. Dataset construction, sampling, licensing and reference standard
4. Evidence models and issue detectors
5. IGAT method (derivation, parameters and alternatives)
6. Experimental design, predeclared metrics, baseline fairness
7. Results with uncertainty and complete failure analysis
8. Ablations and external dataset limitations
9. Human-review effort and reproducibility details
10. Ethics, governance, generalizability, future work

## Potential venues (verify fit and current author instructions)

*IEEE Journal of Biomedical and Health Informatics*, *Computer Methods and Programs in Biomedicine*, *JMIR Medical Informatics*, *IEEE EMBC*.

**Paper readiness today:** insufficient; no real-world research results, expert adjudication, external validation or established novelty advantage has been obtained. Successful coding/test suites alone do not meet these requirements.
