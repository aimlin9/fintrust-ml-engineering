# Testing Strategy

## Week 1 plan (carried forward)
Test the complete workflow from input to output, including valid
records, missing Device_Type/Location values, invalid data types,
missing required fields, unmatched Customer_ID values, and
model/service failures. The goal is to confirm the pipeline handles
expected problems predictably rather than breaking or silently
producing unreliable output.

## Week 2 — technical tests (minimum 5)

| # | Test | Expected Result | Actual Result | Status |
|---|------|------------------|----------------|--------|
| 1 | Valid input | Passes validation, produces a structured prediction | Passed validation, produced a structured prediction (test_valid_transaction_passes) | Pass |
| 2 | Missing values (Device_Type / Location) | Preprocessed to "Unknown", pipeline continues | Filled to "Unknown" by fill_missing, then encoded normally (test_fill_missing_replaces_device_type_and_location) | Pass |
| 3 | Unexpected category | Validation flags/rejects with a clear error | Rejected with an error naming International_Transaction (test_unexpected_category_fails) | Pass |
| 4 | Incorrect data type | Validation rejects before preprocessing | Rejected with an error naming Amount_NGN (test_incorrect_data_type_fails) | Pass |
| 5 | Empty input | Pipeline returns a clear error, does not crash | validate_transaction_batch returns is_valid=False with an "empty" error, no crash (test_empty_input_handled_cleanly) | Pass |

Full automated suite as of Week 2: **32 tests, all passing** (`pytest
tests/ -v`), covering every pipeline stage plus the optional API
component:

| File | Tests | Covers |
|------|-------|--------|
| tests/test_validation.py | 5 | The 5 test types above, at the schema-validation stage |
| tests/test_preprocessing.py | 5 | Missing-value fill, datetime parsing/coercion, categorical encoding, full sequence |
| tests/test_features.py | 3 | Customer/transaction join, unmatched Customer_ID exclusion, model field selection |
| tests/test_ingestion.py | 6 | Valid file load, missing file, empty file — for both customer and transaction loaders |
| tests/test_model_interface.py | 7 | Prediction contract, scoring rule (including the floating-point-safe check), probability cap, missing-amount handling, config loading |
| tests/test_api.py | 6 | /predict and /health endpoints — valid/low-risk transactions, invalid input, unknown customer |

## Week 3 — expanded tests (Part D: output format, reproducibility)

The Week 3 brief's Part D asks explicitly for output-format and
reproducibility tests on top of the existing categories. `src/pipeline.py`
itself (the orchestrator) had never been directly tested — only its
component stages — so `tests/test_pipeline.py` is new, and
`tests/test_model_interface.py` / `tests/test_api.py` were extended to
cover the trained model and the fixed categorical encoding
(`docs/validation-refinement.md` has the full before/after for both).

| # | Test | Expected Result | Actual Result | Status |
|---|------|------------------|----------------|--------|
| 6 | Pipeline output format | Each prediction has exactly the 4 contract fields, valid prediction/probability ranges | Confirmed for all rows (test_run_pipeline_output_format) | Pass |
| 7 | Pipeline reproducibility | Running the same input twice returns identical output | first_run == second_run, byte-for-byte (test_run_pipeline_is_reproducible) | Pass |
| 8 | Pipeline invalid-batch handling | No crash; empty predictions; explicit errors | result["predictions"] == [], errors reference the bad field (test_run_pipeline_returns_errors_for_invalid_batch_without_crashing) | Pass |
| 9 | Trained model loads and predicts | Same two-column contract as the mock model | Confirmed via a tiny deterministic trained bundle (test_trained_risk_model_from_file_loads_and_predicts) | Pass |
| 10 | load_model() picks trained model when present | Returns TrainedRiskModel with the file's version | Confirmed (test_load_model_loads_trained_model_file_when_present) | Pass |
| 11 | load_model() falls back when no model file exists | Returns the mock RiskModel, prints a warning | Confirmed via capsys (test_load_model_falls_back_to_mock_when_file_missing) | Pass |

Full automated suite as of Week 3: **39 tests, all passing**
(`pytest tests/ -v`) — confirmed in the sandbox and independently
re-run on the user's own machine (39 passed, 1 pre-existing benign
warning unrelated to this work: a `StarletteDeprecationWarning` about
the `httpx`/`starlette.testclient` version pairing).

| File | Tests (Week 2 → Week 3) | What changed |
|------|--------------------------|----------------|
| tests/test_validation.py | 5 → 5 | Unchanged |
| tests/test_preprocessing.py | 5 → 5 | Encoding assertions updated for the fixed config-driven mapping |
| tests/test_features.py | 3 → 3 | Unchanged |
| tests/test_ingestion.py | 6 → 6 | Unchanged |
| tests/test_model_interface.py | 7 → 12 | +5: TrainedRiskModel loading/predicting, extra-column handling, load_model()'s trained-vs-fallback branches |
| tests/test_api.py | 6 → 6 | Fixture now injects a known mock model (monkeypatch) so assertions stay deterministic once a real trained model can also be loaded; request path now goes through `preprocess()` directly instead of the deleted `_encode_single_transaction()` workaround |
| tests/test_pipeline.py | 0 → 3 | New: output format, reproducibility, invalid-batch handling at the orchestrator level |

## End-to-end run against the real FinTrust data (Week 2, mock model)

`src/pipeline.py` was run against the actual Week 1 data files
(`data/FinTrust_Customer_Data.csv`, `data/FinTrust_Transaction_Data.csv`
— 1,500 customers, 12,000 transactions):

- **Validation errors: 0** — every transaction record passed schema
  validation.
- **Unmatched Customer_ID: 0** — every transaction's Customer_ID had a
  matching customer record, so the join-exclusion safeguard
  (docs/risks.md) wasn't triggered on this dataset. It remains in place
  for any future data where that isn't true.
- **Predictions returned: 12,000** (one per transaction, none dropped).
- **Prediction distribution (mock model):** 11,898 flagged low-risk
  (0), 102 flagged for review (1) — about 0.85% of transactions.
- **Probability range:** 0.1 to 0.6, median 0.1 — consistent with the
  mock model's placeholder rule (base 0.1, +0.3 for Amount_NGN >
  50,000, +0.2 for international transactions).

This confirms the pipeline runs cleanly end to end on the real dataset
at its current volume, and that the mock model's placeholder logic
behaves as documented — not that its risk flags are meaningful, since
it is not a trained model (see docs/risks.md and
src/model/model_interface.py).

## Training run against the real FinTrust data (Week 3, trained model)

`python -m src.model.train` was run against the same two CSVs (80/20
stratified split, `random_state=42`, 9,600 training rows / 2,400 test
rows):

- **Accuracy:** 0.6079 (sandbox) / 0.6075 (user's machine)
- **Precision:** 0.2751 (sandbox) / 0.2748 (user's machine)
- **Recall:** 0.6128 (both)
- **F1:** 0.3797 (sandbox) / 0.3794 (user's machine)
- **Confusion matrix `[[TN, FP], [FN, TP]]`:** `[[1171, 759], [182,
  288]]` (sandbox) / `[[1170, 760], [182, 288]]` (user's machine)

The one-row difference between environments (Python 3.11.15 in the
sandbox vs. 3.14.6 on the user's machine, different scikit-learn
builds) is normal floating-point/solver variance given identical data,
split and `random_state` — not a bug. Full test suite (`pytest tests/
-v`) passed in both environments: **39 passed**.

This confirms the development model trains and saves reproducibly
end-to-end on the real data, and that its modest precision (see
`docs/risks.md`) is a real, measured property of the model — not an
integration defect.
