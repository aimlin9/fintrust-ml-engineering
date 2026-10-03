# Validation & Refinement Log — Week 3

Per the Week 3 brief's Validation & Refinement requirement, this log
records real development work in the format:

**Initial Output → Test → Finding → Refinement → Re-test → Result**

Two entries are recorded below: the main one (categorical encoding)
was a genuine Week 2 correctness gap found and fixed in Week 3; the
second (model integration) documents the trained-model work the same
way, since it also went through a test → finding → refinement cycle.

---

## Entry 1 — Single-row vs. batch categorical encoding

**Initial Output**

Week 2's `encode_categoricals()` (`src/preprocessing/preprocess.py`)
used pandas' `.astype("category").cat.codes`, which assigns integer
codes relative to whatever category values are *present in the batch
being encoded*. The batch pipeline (`src/pipeline.py`) always ran this
against the full transaction CSV, so it worked there. The API
(`src/service/api.py`) ran it against a single-row DataFrame built
from one request, and worked around the mismatch with a separate,
hardcoded `_encode_single_transaction()` function that only handled
`International_Transaction` and was documented as a known limitation.

**Test**

Traced what `.cat.codes` actually produces for a single-row batch:
for any categorical column, a DataFrame with exactly one row has
exactly one category value present, so `.cat.codes` always assigns it
code `0` — regardless of which actual value it is.

**Finding**

Confirmed: a single transaction with `Channel = "USSD"` and a single
transaction with `Channel = "Web"` would both encode to `Channel = 0`
if `encode_categoricals()` were ever used directly on single-row data,
because each is the only value "present" in its own one-row batch. The
API's workaround avoided this for `International_Transaction` only; no
equivalent protection existed for `Channel`, `Device_Type`, `Location`
or `Transaction_Status` had the API ever needed to encode them
directly. This was a real correctness gap, not just a documentation
note — batch and single-row requests for the same transaction could
disagree on encoded feature values.

**Refinement**

Replaced the batch-relative encoder with a fixed, explicit mapping
defined once in `configs/pipeline_config.yaml`
(`categorical_encodings`), built from the real FinTrust data's actual
unique category values for each column. `encode_categoricals()` now
does `.map(mapping).fillna(-1).astype(int)` per column — the same
function, used by both the batch pipeline and (via `preprocess()`) the
API, always produces the same code for the same value, regardless of
what else is in the batch. An unseen value maps to `-1` instead of
silently colliding with a real code. This also meant `api.py`'s
`_encode_single_transaction()` workaround could be deleted entirely —
the API now calls `preprocess()` directly, the same function the batch
pipeline uses, with no separate encoding path to keep in sync.

**Re-test**

- `tests/test_preprocessing.py` — existing encoding tests updated to
  assert against the fixed config mapping rather than batch-relative
  codes; all pass.
- `tests/test_api.py` — all 6 tests pass against the new `preprocess()`
  call path (fixture updated to inject a known mock model so
  assertions stay deterministic regardless of which model is loaded).
- `tests/test_model_interface.py` — encoding-dependent fixtures
  unaffected; all pass.
- Full suite: `pytest tests/ -v` → **39 passed**, both in the
  sandbox and on the user's own machine.

**Result**

Batch and single-transaction requests for the same data now produce
identical encoded feature values, because they run through the exact
same `preprocess()` function and the same fixed mapping — not two
separately maintained encoders. The Week 2 known limitation
(documented in `docs/week2-project-summary.md`, item 6) is resolved,
not just narrowed.

---

## Entry 2 — Model stage: from placeholder rule to a trained model

**Initial Output**

Week 2's model stage (`src/model/model_interface.py`) was a documented
placeholder, `RiskModel`: a fixed arithmetic rule (base score + bumps
for large/international transactions), standing in for a Data Science
model that was never delivered (solo on this track — see
`docs/risks.md`, "Dependency on Data Science track").

**Test**

Re-read the Week 3 brief, Part C (ML Engineering track): "Where a Data
Science model is available, integrate the model into your workflow. If
another model is not available, use your own appropriate model... for
development purposes." Checked whether a Data Science model artifact
existed anywhere in the shared project materials.

**Finding**

No Data Science model or interface was available to integrate. The
brief explicitly permits training ML Engineering's own development
model in that case, provided it is not represented as another track's
deliverable.

**Refinement**

Wrote `src/model/train.py`: pulls `Risk_Review_Flag` out of the
transaction data *before* it passes through `preprocess()`/
`join_customer_transaction()` (so the same leakage safeguard from
`docs/risks.md` applies to training, not just inference), trains a
`LogisticRegression(class_weight="balanced")` on an 80/20 stratified
split, and saves the fitted model via `joblib`. Added `TrainedRiskModel`
to `model_interface.py`, sharing the exact same `predict()` contract as
the placeholder `RiskModel`, and made `load_model()` choose between
them based on whether `configs/pipeline_config.yaml`'s `model.path`
points to a file that exists — falling back to the placeholder with a
printed warning if not, so a fresh clone never hard-crashes before
`python -m src.model.train` has been run.

**Re-test**

- `python -m src.model.train` run successfully in the sandbox and on
  the user's machine; metrics recorded below.
- `tests/test_model_interface.py` — 5 new tests added covering
  `TrainedRiskModel.from_file`, the shared `predict()` contract,
  extra-column handling, and both branches of `load_model()`'s
  trained-vs-fallback decision (including the printed warning).
- Full suite: **39 passed** in both environments.

**Result**

The pipeline and API now use a real trained model by default, with a
safe fallback when none exists yet. Its actual performance — accuracy
0.608, precision 0.275, recall 0.613, F1 0.380 (sandbox run; the user's
machine reproduced this within normal cross-environment variance, see
`docs/week3-project-summary.md`) — is reported honestly rather than
embellished: it is a development-purpose logistic regression on a
synthetic target, not a production-ready risk model, and is documented
as such in `docs/risks.md` and the README's "Known limitations."
