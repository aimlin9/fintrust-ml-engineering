# Technical Risks

## Status as of Week 3

| Risk | Status | Note |
|------|--------|------|
| Static CSV input | Open, unchanged | Still a static snapshot; interface unchanged. |
| Invalid input data | Mitigated | Unchanged since Week 2; covered by validation tests. |
| Model version mismatch | Mitigated | `model.version`/`model.path` in config; `/health` and every prediction record which model produced it. |
| Unmatched Customer_ID | Mitigated | Unchanged since Week 2. |
| Data leakage | Mitigated, extended | Week 2 mitigation covered inference; Week 3 applies the same safeguard to training (`src/model/train.py` pulls the target out before `preprocess()`/`join_customer_transaction()` run — see `docs/validation-refinement.md`, Entry 2). |
| Dependency on Data Science track | Partially resolved | No Data Science model was delivered (solo on this track). Per the Week 3 brief's explicit allowance, ML Engineering trained its own development model (`src/model/train.py`) rather than continuing to wait on the placeholder. This resolves the *pipeline-integration* half of the risk; it introduces a new, separate limitation below. |
| **New: single-row vs. batch encoding inconsistency** (Week 2 limitation) | **Resolved in Week 3** | Fixed, config-driven categorical mapping (`configs/pipeline_config.yaml`) now used by both the batch pipeline and the API; see `docs/validation-refinement.md`, Entry 1. |
| **New: development model's real performance is modest** | Open, documented | The trained model (logistic regression, see below) has low precision (~0.28) at the recall level it was tuned for. This is reported honestly, not treated as a solved problem — see "Known limitations" below and `docs/week3-project-summary.md`. |

## Full risk register

| Risk | Why It May Matter | Mitigation |
|------|--------------------|------------|
| Static CSV input | The prototype may not represent a continuously operating banking data source. | Ingestion sits behind a clear interface so the CSV source can later be replaced by a database, batch source or streaming source. |
| Invalid input data | Incorrect types, malformed dates or missing required fields could cause unreliable predictions or pipeline failures. | Validate inputs before preprocessing; return explicit validation errors. |
| Model version mismatch | Pipeline code could send inputs using a feature structure that belongs to a different model version. | Track model versions separately from code; record the model version used per prediction. |
| Unmatched Customer_ID | The pipeline may be unable to correctly combine customer and transaction information. | Validate the customer lookup; reject or explicitly flag unmatched records rather than silently proceeding. |
| Data leakage | Information intended only for training (e.g. Risk_Review_Flag) could accidentally enter prediction-time inputs. | Separate target fields from inference features; validate the feature contract before each prediction, and before training (Week 3). |
| Dependency on Data Science track | ML Engineering cannot fully integrate a Data Science model until that track provides a usable artifact/interface. | Define the expected model contract early; use a mock model/interface (`src/model/model_interface.py`) while unavailable; Week 3 trained ML Engineering's own development model under the brief's explicit allowance for this case, with a graceful fallback to the mock if no model file exists. |
| Development model performance is modest | A logistic regression trained for recall over precision will flag many low-risk transactions alongside genuine ones; treating its output as reliable risk assessment would be a mistake. | Report real metrics (not just "it works"); document this plainly in the README, this file, and the Week 3 Project Summary; keep the mock fallback so the pipeline never silently depends on this model being good. |

## Note on the development model

`src/model/train.py` trains a `LogisticRegression(class_weight="balanced")`
on the real FinTrust data (80/20 stratified split, `random_state=42`).
Measured test-set performance (sandbox run; the user's own machine
reproduced this within normal cross-environment variance — see
`docs/week3-project-summary.md`):

- Accuracy: 0.608
- Precision: 0.275
- Recall: 0.613
- F1: 0.380
- Confusion matrix `[[TN, FP], [FN, TP]]`: `[[1171, 759], [182, 288]]`

`class_weight="balanced"` was chosen to avoid the model trivially
predicting "no review" for every transaction (the target is
imbalanced), which pushes recall up at the cost of precision — roughly
3 in 4 flagged transactions are false positives at this setting. This
is disclosed here deliberately rather than only reported as "a model
is now integrated." It is ML Engineering's own development model, not
a Data Science deliverable, and `Risk_Review_Flag` remains a synthetic,
educational label, not a real fraud determination.
