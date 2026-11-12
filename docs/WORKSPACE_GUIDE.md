# MedData Forensics — Research workspace guide

The application is a local research workbench. All pre-import diagrams and example images are **illustrative, nonmedical content**, not research findings. Every module has a distinct purpose and dataset-backed workflow.

| Workspace | Before importing data | After importing / generating data |
|---|---|---|
| Overview | Summary and start controls | Research collection and job activity |
| Dataset DNA | Provenance / source / split schema | Distribution, lineage and samples |
| Forensic Audit | Detector pipeline | Actual findings with inspectable evidence |
| Evidence Graph | Labeled conceptual network | Network of real sample and detector relationships |
| Review Center | Four possible decisions | Append-only reviewer decisions and evidence |
| Shortcut Inspector | Synthetic corner masking example | Frozen-model region sensitivity experiment |
| Counterfactual Lab | Interactive nonmedical brightness/blur/mask example | Image perturbation result on held-out data |
| Cross-Dataset Lab | Source/target compatibility checklist | Evaluated external test collection when compatible |
| Impact Simulator | Frozen test design with no invented metrics | Before / after removal-only comparison |
| Model Failure Explorer | Explanation of the confusion matrix | Baseline results, misclassifications and calibration |
| Reproducibility Engine | Illustrative manifest schema | Recorded manifests, fixed seeds and exportable reports |
| Privacy & Integrity | Local protections and governance information | Same protections plus dataset-specific storage context |

## First use

1. Open the application on `http://127.0.0.1:8765`.
2. Choose **Create synthetic dataset** on any page; it generates nonmedical shapes for workflow testing.
3. Run **Forensic Audit** to find evidence; investigate **Evidence Graph** and **Review Center**.
4. Run the CPU baseline in **Model Failure Explorer** before model-dependent labs.
5. Import an authorized, properly licensed medical research dataset when ready to run real biomedical experiments.

## Interpretation safeguards

- A synthetic visual preview does not imply a trained model or prediction exists.
- A suspected label mismatch is not a verified clinical mislabel.
- The conceptual evidence network shown before dataset import is not computed evidence.
- The Impact Simulator reports no metrics until the corresponding experiment actually runs.
- Results from nonmedical synthetic shapes must not be described as clinical validation.
- Avoid uploading identifiable patient data without institutional authorization and security review.
