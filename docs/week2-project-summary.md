# Week 2 Project Summary — ML Engineering Track

## 1. What I planned to accomplish in Week 2

Per the Week 1 plan (`docs/technical-requirements.md`, `docs/architecture.md`),
Week 2 was scoped to move from architecture on paper to an initial,
working implementation of the pipeline stages defined in Week 1:
Data → Validation → Preprocessing → Feature Preparation → Model →
Prediction → Output → Testing. This meant: a real repository structure,
a schema validator, a preprocessing workflow, a feature-joining stage,
a mock model interface (standing in for the Data Science track's model,
per the dependency risk identified in Week 1), an orchestrator tying
the stages together, at least 5 technical tests, a reproducible setup
(README, requirements.txt), and Git/GitHub evidence of the work.

## 2. What I actually completed

- A project repository (`fintrust-ml-engineering`) with a structure
  that mirrors the pipeline stages: `src/ingestion`, `src/validation`,
  `src/preprocessing`, `src/features`, `src/model`, `src/service`,
  plus `configs/`, `docs/`, `tests/`.
- `src/ingestion/data_loader.py` — loads customer and transaction CSVs,
  with explicit errors for a missing or empty file.
- `src/validation/schema_validator.py` — validates a transaction record
  (required fields, valid `Amount_NGN`, parseable `Transaction_DateTime`,
  `International_Transaction` in the allowed set) and a full batch.
- `src/preprocessing/preprocess.py` — fills missing `Device_Type`/
  `Location` with `"Unknown"`, parses `Transaction_DateTime`, and
  encodes categorical fields.
- `src/features/feature_pipeline.py` — joins customer and transaction
  data on `Customer_ID`, excludes unmatched `Customer_ID` records
  (with a warning) rather than passing them through silently, and
  selects the modelling fields.
- `src/model/model_interface.py` — a documented mock `RiskModel`,
  standing in for the Data Science track's model until it's delivered.
- `src/pipeline.py` — the orchestrator, running every stage in sequence
  and returning structured predictions plus any validation errors.
- `src/service/api.py` — the optional advanced component: a FastAPI
  service (`POST /predict`, `GET /health`) exposing the pipeline as a
  request/response endpoint, reusing the same validation, join, and
  model logic as the batch pipeline.
- 32 automated tests across all six modules (`pytest tests/`), all
  passing.
- The pipeline run end-to-end against the real FinTrust CSVs (1,500
  customers, 12,000 transactions): 0 validation errors, 0 unmatched
  `Customer_ID`s, 12,000 predictions returned.
- `README.md`, `requirements.txt`, and `.gitignore` for reproducibility.
- Work committed to Git in stages and pushed to GitHub
  (`github.com/aimlin9/fintrust-ml-engineering`).

## 3. Tools used

Python, pandas, PyYAML, pytest, FastAPI, Git/GitHub. Config is kept
separate from code (`configs/pipeline_config.yaml`), per the Week 1
version-control requirements.

## 4. Key findings or development outcomes

- The pipeline runs cleanly end to end on the actual FinTrust dataset
  at its current volume (12,000 transactions), with no validation
  failures and no join mismatches — the data is clean on the fronts
  this pipeline checks.
- The mock model's placeholder scoring rule (flagging larger and
  international transactions) produced a plausible-looking but
  entirely synthetic result: ~0.85% of transactions flagged for
  review. This confirms the pipeline is wired together correctly; it
  says nothing about real risk, since no trained model is involved yet.
- Testing surfaced two real implementation bugs before they reached
  production code: an incorrect test assertion that compared an
  already-encoded value against its pre-encoding string, and a
  floating-point equality check that failed due to binary rounding
  (`0.1 + 0.3 + 0.2 != 0.6` exactly in Python). Both were caught by the
  test suite itself, not discovered later — which is the reason the
  tests exist.

## 5. Major challenges encountered

- **Single-row vs. batch categorical encoding.** The batch pipeline's
  encoder (`encode_categoricals`) assigns category codes relative to
  whatever values are present in that batch — correct for scoring a
  full CSV, but wrong for the API's single-transaction requests (a
  lone `"Yes"` would always encode to `0`, since there's nothing else
  in the "batch" to be relative to). This was caught during
  implementation rather than after; see the decision below.
- **Local execution without a shell on the development machine.** All
  code was written and reviewed, then transferred to the local
  Windows repository and executed there (venv, pytest, git) by
  running each command manually and reporting results back, rather
  than through direct remote execution.

## 6. Important decisions made and why

| Decision | Reason | Evidence | Effect |
|---|---|---|---|
| Exclude unmatched `Customer_ID` transactions from the feature set, with a warning, rather than passing them through with null customer fields | Matches the Week 1 risk mitigation for unmatched joins (`docs/risks.md`) | `test_join_excludes_unmatched_customer_id` | A data-quality issue is visible rather than silently degrading predictions |
| Invalid batches stop the pipeline and return errors, rather than partially processing valid rows | Matches the Week 1 technical requirement to reject/flag invalid data explicitly | `run_pipeline`'s early return in `src/pipeline.py` | Predictable failure behaviour; no partial/unreliable output |
| Hardcode a fixed, documented mapping for single-row API encoding instead of reusing the batch-relative `.cat.codes` encoder | The batch encoder is not deterministic for a single row (see challenge above) | Comment in `src/service/api.py::_encode_single_transaction` | The API gives correct predictions today; the real fix (a shared, config-driven encoding scheme with Data Science) is documented as future work rather than hidden |
| Implement the optional API component rather than leaving it as a documented concept only | Time allowed for it, and it exercises the pipeline stages under a different call pattern (single-row vs. batch), which is a useful correctness check on its own | `src/service/api.py`, `tests/test_api.py` (6 tests) | Adds request/response usage as a second, tested way to call the pipeline |

## 7. Changes to my Week 1 approach

No changes to the architecture itself — the pipeline stages match the
Week 1 design exactly (Data → Validation → Preprocessing → Feature
Preparation → Model → Prediction → Output → Testing). The one addition
not fully specified in Week 1 is the concrete choice of FastAPI for the
optional API component; Week 1 only specified the request/response
contract, not a framework.

## 8. Testing or evaluation performed

32 automated tests via `pytest`, covering every stage:

| Stage | Tests | What's covered |
|---|---|---|
| Ingestion | 6 | Valid file load, missing file, empty file (customer + transaction) |
| Validation | 5 | Valid input, missing required field, unexpected category, incorrect data type, empty input |
| Preprocessing | 5 | Missing-value fill, datetime parsing/coercion, categorical encoding, full sequence |
| Features | 3 | Customer/transaction join, unmatched `Customer_ID` exclusion, model field selection |
| Model interface | 7 | Prediction contract, scoring rule, probability cap, missing-amount handling, config loading |
| API/service | 6 | `/predict` and `/health`, valid and low-risk transactions, invalid input, unknown customer |

Full details and the minimum-5 technical test table are in
`docs/testing-strategy.md`, along with the end-to-end run results
against the real FinTrust data.

## 9. Key limitations

- The model is a documented mock (`src/model/model_interface.py`) —
  its predictions are placeholder logic, not a trained model's output,
  and must not be treated as real risk assessment. This is an
  intentional Week 2 scope decision, not an oversight (see Week 1
  dependency risk).
- The API's single-row categorical encoding is a deliberate, narrower
  substitute for the batch encoder, not a general fix — see the
  decision above and the comment in `src/service/api.py`.
- No trained-model integration yet; that depends on the Data Science
  track delivering a model artifact and interface (Week 1 dependency
  risk, unchanged).
- The pipeline has been run against one dataset snapshot (12,000
  transactions); performance at larger volumes or against a live/
  streaming source is untested.

## 10. Remaining work

- Integrate the real trained model once Data Science delivers it
  (only `src/model/model_interface.py` should need to change).
- Agree a fixed, shared category-to-code encoding scheme with Data
  Science so the batch pipeline and the API encode consistently,
  replacing the current single-row workaround.
- Expand test coverage for the API's error paths (e.g. malformed
  JSON, wrong field types) if the service moves beyond a Week 2
  concept.

## 11. Proposed focus for Week 3

- Formal cross-track collaboration begins in Week 2's successor —
  align the model interface contract with whatever Data Science
  produces.
- Harden the API/service component if it's carried forward (auth,
  logging, error responses beyond the current 422/404 cases).
- Revisit the categorical-encoding limitation as a shared decision
  with Data Science rather than an ML-Engineering-only workaround.
