# Week 4 — Final End-to-End Testing & Validation

Per the Week 4 brief (ML Engineering, Part B) and the general Final
Testing & Validation requirement (Section 9), this documents the
complete test → result → action cycle for every required scenario,
plus the one real gap found and fixed this week.

## End-to-end test table

| Test | Expected Result | Actual Result | Pass/Fail | Action Taken |
|---|---|---|---|---|
| Valid input | Passes validation, produces a structured prediction | Passed validation, prediction returned with the 4-field contract (both the batch pipeline and the API) | Pass | None needed |
| Missing values (Device_Type / Location) | Filled to "Unknown", pipeline continues rather than dropping the record | Filled to "Unknown" by `fill_missing`, then encoded normally via the fixed mapping | Pass | None needed |
| Unexpected categories | Rejected with a clear, specific error before preprocessing | Rejected, error names the offending field (batch: `validate_transaction_batch`; API: 422 with the same message) | Pass | None needed |
| Invalid data types | Rejected before preprocessing | Rejected, error names the field (e.g. non-numeric `Amount_NGN`) | Pass | None needed |
| Empty input | Returns a clear error, does not crash | `is_valid=False` with an explicit "empty" error, pipeline returns `predictions: []` | Pass | None needed |
| Model loading | Loads the trained model file when present; falls back to the placeholder with a warning when it's missing, in either case without crashing | Both branches confirmed (`test_load_model_loads_trained_model_file_when_present`, `test_load_model_falls_back_to_mock_when_file_missing`) | Pass | None needed |
| Prediction generation | Every input row produces exactly one prediction + one probability | Confirmed for both the placeholder and the trained model, batch and single-row | Pass | None needed |
| Output format | Each prediction has exactly `Transaction_ID`, `Customer_ID`, `risk_review_prediction`, `risk_review_probability`, with valid ranges | Confirmed at the orchestrator level (`test_run_pipeline_output_format`) | Pass | None needed |
| Reproducibility | Identical input run twice returns identical output | Confirmed byte-for-byte (`test_run_pipeline_is_reproducible`); the training script itself was also independently re-run on a second machine and reproduced its metrics within normal floating-point variance | Pass | None needed |
| Error handling (API, added this week) | An unexpected failure (not a validation or unknown-customer case) should not leak internals to the caller | Initially, an unhandled exception in `model.predict()` would propagate as FastAPI's default 500 page, including a stack trace | **Fail, then Pass** | Added a global exception handler (see below) |

Full automated suite: **40 tests, all passing** (`pytest tests/ -v`),
up from 39 at the end of Week 3 — the one addition is the new
error-handling test.

## Validation & Refinement entry — API error handling

**Initial Output.** The API (`src/service/api.py`) handled two error
cases explicitly: `422` for validation failures and `404` for an
unmatched `Customer_ID`. Anything else that could go wrong inside
`predict()` — a corrupted model file, an unexpected data shape, a bug
— had no handler, so it would propagate to FastAPI's default
exception behaviour.

**Test.** Simulated an unexpected failure directly: swapped the loaded
model for one whose `predict()` raises `RuntimeError`, then sent a
normally-valid request.

**Finding.** The request failed with FastAPI's default unhandled-
exception response — a `500` that, outside of a test harness, would
expose an internal stack trace to the caller. This is not acceptable
for a service component described as "final" (brief, Part D: finalize
the API, demonstrate error handling).

**Refinement.** Added a global exception handler
(`unhandled_exception_handler`, registered via
`@app.exception_handler(Exception)`) that logs the real exception
server-side and returns a generic, safe `{"detail": "Internal error
while processing the request."}` with status `500` to the caller —
without changing the existing, more specific `422`/`404` behaviour,
which FastAPI still handles first.

**Re-test.** Added
`tests/test_api.py::test_predict_unexpected_error_returns_safe_500`,
which injects the same broken model and asserts the response is now
the clean, generic `500`. Full suite re-run: **40 passed**.

**Final Result.** The API now has three distinct, intentional error
paths — `422` (bad input), `404` (unknown customer), `500` (anything
unexpected) — and none of them leak internal detail to the caller.
This closes the one real gap in "Part D — API/Service" for a final
submission.
