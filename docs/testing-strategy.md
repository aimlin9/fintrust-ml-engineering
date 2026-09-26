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

Full automated suite: **32 tests, all passing** (`pytest tests/ -v`), covering
every pipeline stage plus the optional API component:

| File | Tests | Covers |
|------|-------|--------|
| tests/test_validation.py | 5 | The 5 test types above, at the schema-validation stage |
| tests/test_preprocessing.py | 5 | Missing-value fill, datetime parsing/coercion, categorical encoding, full sequence |
| tests/test_features.py | 3 | Customer/transaction join, unmatched Customer_ID exclusion, model field selection |
| tests/test_ingestion.py | 6 | Valid file load, missing file, empty file — for both customer and transaction loaders |
| tests/test_model_interface.py | 7 | Prediction contract, scoring rule (including the floating-point-safe check), probability cap, missing-amount handling, config loading |
| tests/test_api.py | 6 | /predict and /health endpoints — valid/low-risk transactions, invalid input, unknown customer |

## End-to-end run against the real FinTrust data

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
