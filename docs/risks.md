# Technical Risks

## Status as of Week 4 (final)

| Risk | Status | Note |
|------|--------|------|
| Static CSV input | Open, unchanged | Still a static snapshot; interface unchanged. Not revisited in Week 4 — out of scope for a solo, time-boxed track. |
| Invalid input data | Mitigated | Unchanged since Week 2; covered by validation tests, both batch and API. |
| Model version mismatch | Mitigated | `model.version`/`model.path` in config; `/health` and every prediction record which model produced it. |
| Unmatched Customer_ID | Mitigated | Unchanged since Week 2. |
| Data leakage | Mitigated, extended | Week 2 mitigation covered inference; Week 3 extended it to training (`src/model/train.py` pulls the target out before `preprocess()`/`join_customer_transaction()` run). Unchanged in Week 4. |
| Dependency on Data Science track | Closed for this submission | No Data Science model or interface was received at any point across Weeks 1–4 (confirmed again in Week 4 — still solo on this track). ML Engineering's own development model stands as the final model for this submission, honestly labelled as such throughout. If a Data Science model is handed over after submission, `load_model()` is the single integration point. |
| Single-row vs. batch encoding inconsistency (Week 2 limitation) | Resolved in Week 3 | Fixed, config-driven categorical mapping (`configs/pipeline_config.yaml`) used by both the batch pipeline and the API; see `docs/validation-refinement.md`, Entry 1. Unchanged in Week 4. |
| Development model's real performance is modest | Open, documented | The trained model (logistic regression, see below) has low precision (~0.28) at the recall level it was tuned for. Reported honestly as a final limitation, not treated as solved. No further tuning was attempted in Week 4 — see "Final limitations" below and `docs/week4-project-summary.md` for why. |
| **New: API unhandled-exception leakage** | **Resolved in Week 4** | An unexpected failure (not a validation or unknown-customer case) previously reached the caller as FastAPI's default 500 page. Fixed with a global exception handler; see `docs/week4-final-testing.md`. |

## Final limitations and responsible-use statement (Week 4, Section 11)

This submission is an educational prototype, not a production banking
system, and should not be read as one:

- **FinTrust Digital Bank is a fictional organisation**, built for this
  internship programme. Nothing here reflects a real bank's data,
  policies, or systems.
- **All data is synthetic.** `FinTrust_Customer_Data.csv` and
  `FinTrust_Transaction_Data.csv` were generated for this exercise.
- **`Risk_Review_Flag` is a synthetic, educational target.** A `1`
  prediction from this pipeline is not evidence of fraud, financial
  crime, or any real risk event, and must never be presented as such.
- **This is not a production-ready system.** It has not been load-
  tested, has no authentication on the API, and has only been
  validated against one dataset snapshot (12,000 transactions).
- **The model's precision is low (~0.28).** At the current setting,
  roughly 3 in 4 flagged transactions are false positives. Any
  downstream use of its output should treat predictions as a weak
  signal to investigate, not a verdict.
- **This component makes no personalised financial, investment, or
  legal recommendations** — it returns a binary review flag and a
  probability, nothing else, and that scope was intentionally kept
  narrow.
- **Unsupported assumption, stated plainly:** that the real FinTrust
  data's category values and distributions (6 transaction types, 5
  channels, ~20% positive rate, etc.) are representative of ongoing
  production traffic. This was not validated against any out-of-sample
  period, because none exists for this synthetic dataset.

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
