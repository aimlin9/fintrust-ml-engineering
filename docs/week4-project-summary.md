# Week 4 Final Project Summary — ML Engineering Track

## 1. The FinTrust problem

FinTrust Digital Bank (fictional) wants to use data, machine learning
and generative AI to better understand customer and transaction
behaviour, support risk-related decision-making, improve operational
processes and strengthen digital customer support. ML Engineering's
role across the four weeks has been to design and deliver the
technical workflow that turns raw transaction and customer data into a
structured, risk-review prediction — reliably, reproducibly, and ready
for other components to call.

## 2. Review of Weeks 1–3

- **Week 1** produced the architecture (Data → Validation →
  Preprocessing → Feature Preparation → Model → Prediction → Output →
  Testing), technical requirements, repository structure, risk
  register, and initial testing strategy — all on paper, nothing
  running yet.
- **Week 2** turned that into a working repository: every pipeline
  stage implemented, a mock model standing in for a Data Science model
  that hadn't arrived, an optional FastAPI service, and 32 passing
  tests. It also surfaced a real limitation it didn't fully resolve: a
  single-row API request could encode categorical fields differently
  than the same transaction encoded as part of a batch.
- **Week 3** resolved that limitation with a fixed, config-driven
  encoding scheme shared by both paths, and trained ML Engineering's
  own development model (`src/model/train.py`) since no Data Science
  model had been delivered — permitted explicitly by that week's
  brief. Test count reached 39.
- Reviewing this against Week 4's requirement to "identify what needs
  to be completed, corrected or improved": the architecture has held
  unchanged since Week 1, the two real gaps from Week 2 (encoding
  inconsistency, no trained model) were both closed in Week 3, and the
  one gap found going into Week 4 was the API's handling of genuinely
  unexpected errors — addressed below.

## 3. What was finalized in Week 4

- Added a global exception handler to the API so any unexpected
  failure returns a safe, generic `500` instead of leaking an internal
  stack trace — the one real remaining gap in "finalize the API"
  (brief, Part D).
- Added a test for that handler; full suite now **40 tests, all
  passing**.
- Wrote the explicit end-to-end test table required by Part B
  (`docs/week4-final-testing.md`), covering all nine named scenarios
  plus the error-handling fix, each with a documented
  Test → Expected → Actual → Pass/Fail → Action Taken row.
- Reconfirmed the Data Science dependency status directly rather than
  assuming it was still accurate: no model or interface has been
  received at any point across all four weeks. Documented this
  explicitly in `docs/week4-integration-note.md` rather than
  implying integration that didn't happen.
- Brought `docs/risks.md` to a final state: closed the Data Science
  dependency risk (closed for this submission, not "pending"), closed
  the new API error-leakage risk, and added an explicit final
  limitations / responsible-use statement.
- Updated `README.md`'s status to Week 4 / final submission, with a
  documentation index so a reviewer can find everything.

No change was made to the core architecture, the pipeline stages, or
the trained model itself this week — Week 4's brief frames this stage
as test, refine, finalize, not rebuild, and the one thing worth fixing
was fixed.

## 4. Tools used

Python, pandas, scikit-learn, joblib, PyYAML, pytest, FastAPI,
Git/GitHub — unchanged from Week 2–3.

## 5. Key findings or results

- The API error-handling gap was a real one, not a formality: before
  this week's fix, an unhandled exception reached the caller as a raw
  FastAPI error page. It's now one of three deliberate, distinct error
  paths (`422`, `404`, `500`), none of which expose internal detail.
- Re-confirming the Data Science dependency status (rather than
  assuming Week 3's note still held) cost one direct question and
  prevented a stale or overstated integration claim in the final
  submission — worth doing explicitly rather than carrying forward an
  old assumption into a final deliverable.
- The development model's measured performance (accuracy 0.608,
  precision 0.275, recall 0.613, F1 0.380 — see `docs/risks.md`) is
  unchanged from Week 3; no retraining or tuning was attempted this
  week, and that choice is itself documented below rather than left
  implicit.

## 6. Testing and validation performed

40 automated tests via `pytest` (up from 39 in Week 3), plus the
explicit scenario-by-scenario table required by the Week 4 brief. Full
details are in `docs/week4-final-testing.md`; the underlying test
breakdown by file is unchanged from Week 3 except for one new test in
`tests/test_api.py`. See `docs/testing-strategy.md` for the complete
by-file history across all four weeks.

## 7. Improvements made

- Closed the API's only remaining error-handling gap.
- Converted an implicit assumption (no Data Science model) into an
  explicitly re-checked, dated fact for the final submission.
- Brought the risk register and README to a genuinely final state,
  rather than leaving Week 3's "open" items unaddressed going into
  submission.

## 8. Major challenges encountered

- **Confirming a negative is easy to skip.** It would have been easy
  to carry Week 3's "no Data Science model" note forward unchecked
  into the final submission. Re-confirming it directly (rather than
  assuming) was a small but deliberate step to avoid an inaccurate
  final claim.
- **Deciding what *not* to do.** With the model's precision still low,
  there was a temptation to spend Week 4 trying to improve it.
  Weighed against the brief's actual Week 4 ask ("test → validate →
  refine → finalize", not "improve model accuracy"), the better use of
  limited time was finishing testing, documentation, and the one real
  code gap — see the decision below.
- **Local execution without a shell on the development machine.**
  Unchanged since Week 2 — code and docs are written and reviewed
  here, then run on my own machine (venv, pytest, git) with results
  reported back for review.

## 9. Important decisions made and why

| Decision | Reason | Evidence | Effect |
|---|---|---|---|
| Add a global exception handler rather than per-endpoint try/except blocks | One handler covers every current and future endpoint consistently; per-endpoint handling would need to be remembered and repeated | `src/service/api.py::unhandled_exception_handler`, `tests/test_api.py::test_predict_unexpected_error_returns_safe_500` | A new endpoint added later inherits safe error handling automatically |
| Do not attempt to improve the development model's precision this week | Week 4's brief frames this stage as testing/validation/finalization for ML Engineering, not model improvement (that's squarely Data Science's Part B); time was better spent closing the real remaining gaps (API error handling, documentation) | `docs/risks.md` final limitations | The model's known weakness is disclosed, not hidden behind last-minute, undocumented tuning |
| Re-confirm the Data Science dependency status directly instead of assuming Week 3's note still applied | A final submission should not carry forward a stale assumption, however small the chance it had changed | `docs/week4-integration-note.md` | The final integration claim is accurate and dated, not inherited |
| Keep the architecture and pipeline stages unchanged from Week 1–3 | They have held without needing revision since Week 1; Week 4 is "finalize," not "redesign" | `docs/architecture.md` (unchanged) | Stability — nothing was changed that didn't need changing |

## 10. How this connects to the wider FinTrust solution

Per the brief's integration flow (Customer & Transaction Data →
Analytics Findings & KPIs → Predictive Risk Intelligence → **ML
Workflow/Service** → Knowledge-Based GenAI Support → Integrated
FinTrust Solution), this submission is the ML Workflow/Service stage.
It is complete and internally consistent — a reviewer can clone the
repository, install dependencies, train the model, run the pipeline or
the API, and get a structured, reproducible risk-review prediction. It
was not assembled from another track's actual output and does not
claim to be, since none was received — see
`docs/week4-integration-note.md` for the full, honest account of that.

## 11. Remaining limitations

See `docs/risks.md`'s final limitations and responsible-use statement
for the complete list. In short: synthetic data and target, a
development-only model with modest precision, no production hardening
(auth, load testing), and validation against a single dataset snapshot
only.

## 12. Key lessons learned

- **Finishing well is a different skill from building.** Weeks 2–3
  were mostly about building things that didn't exist yet; Week 4 was
  about checking what already existed actually held up, and fixing the
  one thing that didn't — a smaller but no less real kind of work.
- **"Document it rather than hide it" compounds.** Every week this
  project disclosed a real weakness (Week 2's encoding bug, Week 3's
  model precision, Week 4's error handling) instead of glossing over
  it, and every week that made the next week's actual problem easier
  to find, because nothing was buried under an inflated status update.
- **A stale assumption is cheap to re-check and expensive to carry
  into a final submission unchecked.** The Data Science dependency
  status took one direct question to re-confirm; getting it wrong in
  the final write-up would have been a real, avoidable inaccuracy.

## 13. Recommendations for future work

- If a Data Science model is ever delivered, integrate it behind the
  existing `load_model()` contract — that interface was deliberately
  kept stable across all four weeks for exactly this handoff.
- If this pipeline is extended beyond the internship, prioritize: API
  authentication, load testing at realistic transaction volumes, and
  a genuine attempt at improving the development model's precision
  (feature engineering, threshold tuning, or a different algorithm)
  rather than accepting Week 3–4's baseline indefinitely.
- Keep the pattern established here — disclose real limitations
  plainly, test the orchestrator as well as its parts, and treat
  "finalize" as a distinct, real phase of work rather than a formality
  — for any future track of this kind.
