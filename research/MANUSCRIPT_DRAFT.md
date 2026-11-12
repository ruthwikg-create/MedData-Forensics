# Evidence-Guided Prioritization of Data Integrity Risks in Biomedical Image Datasets: Development and Experimental Evaluation of MedData Forensics

**Draft status:** Methods-oriented outline; **no validated biomedical findings are available yet**. Do not submit this draft as a completed study. All result cells below require verified experimental data.

## Abstract — structured writing template

**Background:** Biomedical imaging AI can be sensitive to duplicate records, data leakage, annotation uncertainty and acquisition-related artifacts. Existing auditing systems identify several such problems, but it remains unclear when particular findings warrant reviewer attention and whether their resolution improves independently evaluated model reliability.

**Objective:** Evaluate whether a proposed evidence-guided, cost-aware triage approach can improve the discovery of independently verified, consequential dataset defects under fixed reviewer budgets compared with existing ranking strategies.

**Methods:** [Specify evaluated biomedical datasets, source licensing, clinical annotation reference standard, sample size, partitioning policy, candidate detectors, baselines, reviewer protocol and prespecified statistical analysis.]

**Results:** [NOT YET AVAILABLE. Insert only actual outcomes, confidence intervals, false positives, per-dataset variability and negative findings.]

**Conclusions:** [NOT YET AVAILABLE. Do not assume superiority or clinical validity.]

## 1. Introduction

- Explain how medical-image model estimates can become unreliable due to data problems and correlated samples.
- Distinguish data-quality triage from diagnosis and from clinical deployment.
- Review relevant methods (Confident Learning, Cleanlab, G-AUDIT, dataset provenance analyses).
- State precise falsifiable hypothesis and proposed contribution, without 'first ever' language.

## 2. Related work and novelty review

| Existing method | Problem addressed | Specific fair comparison with IGAT | Source |
|---|---|---|---|
| Confident Learning | Potential label issues | Training-only out-of-fold label quality ranking | https://research.google/pubs/confident-learning-estimating-uncertainty-in-dataset-labels/ |
| Cleanlab Datalab | Labels, outliers, duplicates, data-quality flags | Confident learning baseline under same review budget | https://docs.cleanlab.ai/stable/tutorials/datalab/datalab_quickstart.html |
| G-AUDIT | Potential shortcut/dataset bias detection | Source/acquisition risk context; do not conflate with triage | https://www.nature.com/articles/s41746-026-02807-y |
| MedMNIST-C | Robustness to image corruption | Controlled stress-test design | https://arxiv.org/abs/2406.17536 |

## 3. Materials and methods

### 3.1 Datasets and reference labels

[Document names, source versions, licenses, accession identifiers, de-identification status, group semantics, inclusion/exclusion rules, splits, and annotation reference standards. Include a reproducible data lineage manifest.]

### 3.2 Candidate detectors

SHA256, decoded-pixel hash, pHash+SSIM, source/group overlap, training-only OOF label suspicion. Report detector thresholds, retrieval caps, per-type sensitivity and shortcomings. Treat outputs as hypotheses.

### 3.3 IGAT

Current pre-study implementation uses a fixed weighted heuristic. Future study may replace weights using development-data tuning only. Freeze the method before evaluating independent test cases. Record explanatory evidence for each queued concern.

### 3.4 Baselines and reviewer protocol

Random, confidence, severity, Cleanlab when applicable. Fix review budgets, cost model, matching candidate pool, group-level adjudication, blinded review, interrater agreement and tie handling.

### 3.5 Downstream model evaluation

Use documented training/validation/test partitions and the same model family, feature extractor and random seeds for all ablations. Do not tune remediation using final test results. Report paired metrics and uncertainty, as well as cases where a change reduces performance.

### 3.6 Statistical analysis

Specify primary endpoint, data hierarchy, alpha control/multiple testing policy and confidence interval method before study. Avoid patient-independence assumptions with multiple images per patient or lesion.

## 4. Results — blank template, do not fabricate

| Dataset | N | Verified issue types | Reviewer time | IGAT yield@k | Best baseline yield@k | Paired difference (95% CI) |
|---|---:|---|---|---|---|---|
| [Dataset A] | — | — | — | — | — | — |
| [Dataset B] | — | — | — | — | — | — |

| Dataset | Intervention | Original macro-F1 (95% CI) | Corrected macro-F1 (95% CI) | Change | Cautions |
|---|---|---|---|---|---|
| [Dataset A] | [Documented training-only correction] | — | — | — | — |
| [Dataset B] | [Documented training-only correction] | — | — | — | — |

## 5. Discussion

Present findings only after analysis, including null results, uncertainty, false positives, limitations of ranking confidence, and clinical heterogeneity. Explain why improved audit triage does **not** itself imply a clinically validated AI system.

## 6. Limitations

Public dataset licensing, group semantics, annotation ambiguity, underspecified site/acquisition labels, incomplete demographic metadata, reviewer variability, model dependence, approximation and compute caps, and lack of prospective clinical validation.

## 7. Ethics, reproducibility and materials

Report data governance, permitted sharing, de-identification, participant/expert requirements if applicable, code revision, reproducibility manifests, datasets and parameter configurations. Do not redistribute restricted images with the public repository.

## 8. References and target venue

Fill in a complete citation style after checking each original paper and choosing a target venue. Follow CLAIM 2024 as relevant for medical imaging AI reporting. Possible venues include IEEE JBHI, Computer Methods and Programs in Biomedicine, and JMIR Medical Informatics, subject to actual contribution and current author instructions.
