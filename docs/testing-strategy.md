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
| 1 | Valid input | Passes validation, produces a structured prediction | TBD | TBD |
| 2 | Missing values (Device_Type / Location) | Preprocessed to "Unknown", pipeline continues | TBD | TBD |
| 3 | Unexpected category | Validation flags/rejects with a clear error | TBD | TBD |
| 4 | Incorrect data type | Validation rejects before preprocessing | TBD | TBD |
| 5 | Empty input | Pipeline returns a clear error, does not crash | TBD | TBD |

Fill in Actual Result / Status once the tests are implemented and run
(`pytest tests/`).
