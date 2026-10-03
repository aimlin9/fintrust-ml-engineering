# Week 3 Project Summary — ML Engineering Track

## 1. What I planned to accomplish in Week 3

Per the Week 2 proposed focus and the Week 3 brief (Part C, ML
Engineering track), Week 3 was scoped to: review the Week 2 plan
against what was actually built; integrate a model into the live
workflow — a Data Science model if one was available, otherwise ML
Engineering's own development model, built honestly as development-
purpose only; resolve the Week 2 known limitation around single-row
categorical encoding rather than carrying it forward again;
expand the test suite (Part D: output format, reproducibility, on top
of the existing categories); update the API/service layer to use the
real model path end to end; and produce the required Validation &
Refinement log, updated risk/testing documentation, and a Week 3
Project Summary.

## 2. What I actually completed

- Reviewed the Week 2 plan against Week 2's actual output: the
  architecture held exactly as designed; the two carried-forward items
  (model integration, the encoding limitation) are both addressed
  below rather than deferred again.
- `src/model/train.py` (new) — trains ML Engineering's own development
  model (`LogisticRegression`, `class_weight="balanced"`) on the real
  FinTrust data, with the same data-leakage safeguard from Week 1's
  risk register applied to training, not just inference. No Data
  Science model was available to integrate (solo on this track), which
  the Week 3 brief explicitly anticipates and allows for.
- `src/model/model_interface.py` — added `TrainedRiskModel`, sharing
  the exact prediction contract as the Week 2 placeholder `RiskModel`;
  `load_model()` now loads the trained model file when present and
  falls back to the placeholder with a printed warning when it isn't,
  so a fresh clone never breaks before training has been run.
- `configs/pipeline_config.yaml` — added a fixed, explicit
  `categorical_encodings` mapping built from the real data's actual
  category values, resolving the Week 2 single-row-encoding limitation
  for good rather than extending the old workaround.
- `src/preprocessing/preprocess.py` — `encode_categoricals()` rewritten
  to use the fixed mapping; now produces identical codes for the same
  value regardless of batch size or composition.
- `src/service/api.py` — deleted the old `_encode_single_transaction()`
  workaround entirely; the API now calls `preprocess()` and
  `build_features()` directly, the exact same functions the batch
  pipeline uses, closing the batch/API consistency gap for good.
- 7 new automated tests (5 in `tests/test_model_interface.py`, covering
  the trained model and both branches of the fallback decision; 3 in
  the new `tests/test_pipeline.py`, the first direct tests of the
  orchestrator itself — output format and reproducibility, per Part D).
- `tests/test_api.py` updated so its assertions stay deterministic
  (inject a known mock model) regardless of which model is actually
  configured.
- Full suite run end-to-end: **39 tests, all passing**, confirmed both
  in development and independently on my own machine.
- `docs/validation-refinement.md` (new) — the required Validation &
  Refinement log, in the brief's Initial Output → Test → Finding →
  Refinement → Re-test → Result format, covering both changes above.
- `docs/risks.md`, `docs/testing-strategy.md`, `README.md` updated to
  reflect Week 3's actual state.
- Work committed to Git in logical stages and pushed to GitHub.

## 3. Major development activities

- Designing and training a real classification model end to end:
  feature selection, leakage-safe target extraction, train/test split,
  training, evaluation, and serialization — not just wiring up a
  placeholder.
- Diagnosing and fixing a genuine encoding-consistency bug between two
  different call paths (batch CSV vs. single-row API request) that
  Week 2 had documented but not resolved.
- Refactoring the API to remove a standalone workaround in favor of
  reusing the pipeline's own shared functions, reducing the surface
  area that could drift out of sync in the future.
- Writing tests that target the orchestrator itself, not just its
  component stages, closing a real coverage gap from Week 2.

## 4. Key findings or results

- The single-row encoding issue was a real correctness gap, not a
  cosmetic one: before the fix, any categorical value in a one-row
  API request would always encode to `0` (see
  `docs/validation-refinement.md`, Entry 1), regardless of its actual
  value. This is now fixed for every categorical column, not just the
  one the Week 2 workaround happened to cover.
- The trained development model achieves recall 0.613 at precision
  0.275 (accuracy 0.608, F1 0.380) on a held-out 20% split of the real
  data. `class_weight="balanced"` was chosen deliberately to avoid the
  trivial "predict no review for everything" outcome on an imbalanced
  target, at the cost of a high false-positive rate. This is reported
  as-is; it is a development-purpose baseline, not a tuned production
  model.
- Running the training script on my own machine reproduced the
  sandbox's metrics within normal cross-environment variance (different
  Python/scikit-learn builds, identical data/split/`random_state`) —
  confirming the training process itself is reproducible, not just
  lucky in one environment.

## 5. Testing and validation performed

39 automated tests via `pytest` (up from 32 in Week 2):

| Stage | Tests | What's covered |
|---|---|---|
| Ingestion | 6 | Unchanged from Week 2 |
| Validation | 5 | Unchanged from Week 2 |
| Preprocessing | 5 | Updated for the fixed config-driven encoding |
| Features | 3 | Unchanged from Week 2 |
| Model interface | 12 | Week 2's 7 placeholder-model tests + 5 new trained-model/fallback tests |
| API/service | 6 | Updated fixture (deterministic mock model injection); same endpoint coverage as Week 2 |
| Pipeline (orchestrator) | 3 | New: output format, reproducibility, invalid-batch handling |

Full details, the before/after test table, and the training-run
results are in `docs/testing-strategy.md`. The required
Initial Output → Test → Finding → Refinement → Re-test → Result
write-ups are in `docs/validation-refinement.md`.

## 6. Improvements made

- Resolved the Week 2 single-row encoding limitation rather than
  re-documenting it as a known limitation a second time.
- Replaced the placeholder model with a real trained one in the live
  pipeline/API path, with a documented, tested fallback.
- Removed a standalone workaround function (`_encode_single_transaction`)
  in favor of one shared code path for batch and single-row requests.
- Added direct tests of the orchestrator (`src/pipeline.py`), closing a
  coverage gap that existed since Week 2.
- Updated the README's reproducibility section to reflect the new
  training step and the graceful fallback behaviour.

## 7. Major challenges encountered

- **No Data Science model to integrate.** Being solo on the ML
  Engineering track meant there was no cross-track model artifact to
  wire in, as the Week 3 brief's primary path for Part C describes.
  The brief explicitly allows training an own development model in
  that situation, which is what was done — documented clearly as such,
  not presented as a Data Science deliverable.
- **Confirming the encoding fix didn't just move the bug.** Because
  the old single-row workaround "worked" for the one column it
  covered, it was important to verify the fix handles every
  categorical column, not only `International_Transaction` — done by
  tracing `.cat.codes`'s actual behaviour on a one-row batch (see
  `docs/validation-refinement.md`, Entry 1) rather than assuming the
  old bug was narrower than it was.
- **Local execution without a shell on the development machine.**
  Unchanged from Week 2 — all code was written and reviewed here, then
  run on my own machine (venv, pytest, `python -m src.model.train`,
  git) with results reported back for review.

## 8. Important decisions made and why

| Decision | Reason | Evidence | Effect |
|---|---|---|---|
| Train ML Engineering's own development model instead of waiting for a Data Science artifact | Week 3 brief (Part C) explicitly permits this when no Data Science model is available; no cross-track collaboration is required until Week 2+ and none was offered | `src/model/train.py`, `docs/risks.md` | The pipeline runs a real model today, honestly labelled as a development-purpose one, rather than staying on the placeholder indefinitely |
| Replace batch-relative `.cat.codes` encoding with a fixed, explicit config mapping | `.cat.codes` is not deterministic across different batch sizes/compositions — a real correctness gap, not a style preference | `docs/validation-refinement.md`, Entry 1; `tests/test_preprocessing.py`, `tests/test_api.py` | Batch and single-row requests now always agree on encoded feature values |
| Delete `_encode_single_transaction()` entirely rather than patching it | The real fix (a shared encoder) makes the workaround redundant; keeping both would leave two paths that could drift apart again | `src/service/api.py` diff | One encoding path to maintain and test, not two |
| Keep the placeholder `RiskModel` as an automatic fallback rather than requiring the trained file to exist | A fresh clone shouldn't crash before `python -m src.model.train` has been run | `load_model()`, `tests/test_model_interface.py::test_load_model_falls_back_to_mock_when_file_missing` | Reproducibility (Part F) holds even before training has happened |
| Use `class_weight="balanced"` rather than leaving the default | The target is imbalanced (~20% positive); the default setting would likely predict "no review" for nearly everything | Reported metrics in `docs/risks.md`/`docs/testing-strategy.md` | Higher recall, lower precision — an explicit, disclosed trade-off rather than a hidden one |

## 9. Remaining limitations

- The development model's precision is low (0.275) at its current
  recall level; it is not tuned or validated to a production standard,
  and is documented plainly as such (see `docs/risks.md`).
- The model is still ML Engineering's own development artifact, not a
  Data Science deliverable — if Data Science produces a model later,
  only `src/model/model_interface.py` (and possibly `train.py`) should
  need to change, per the original Week 1/2 design intent.
- The pipeline has still only been run against one dataset snapshot
  (12,000 transactions); performance and training time at larger
  volumes remain untested.
- No hyperparameter tuning, cross-validation, or feature-engineering
  beyond the original feature set has been attempted — this was scoped
  as a development-purpose baseline, not a tuned model.

## 10. What must be completed in Week 4

- If a Data Science model becomes available via cross-track
  collaboration, integrate it behind the existing `load_model()`
  contract, retiring or keeping `train.py`'s model as a documented
  fallback.
- Consider basic model-quality improvements (feature engineering,
  threshold tuning, or a different algorithm) if time allows, since the
  current model's precision is low enough to be worth revisiting.
- Harden the API/service component if it's carried into Week 4 (auth,
  logging, structured error responses beyond the current 422/404
  cases) — unchanged from the Week 2 proposal, not yet addressed.
- Finalize Week 4 integration/demo materials and any remaining
  cross-track alignment now that formal collaboration is active.

## 11. Final-week priorities

- Treat any Data Science model handoff as the top priority if one
  arrives, since the model-interface contract was deliberately kept
  stable to make that swap low-risk.
- Keep reporting model performance honestly rather than polishing the
  presentation of a model that is, by design, a development baseline.
- Finish any remaining documentation/demo requirements for final
  submission (Week 4 brief, once available).
