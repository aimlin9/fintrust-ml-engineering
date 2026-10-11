# FinTrust ML Risk-Review Pipeline

Machine Learning Engineering track submission for the AnalystLab Africa
Experience Lab Internship Programme — FinTrust Digital Bank project.

Designs and implements the technical pipeline that takes FinTrust
transaction and customer data, validates and preprocesses it, prepares
features, runs it through a risk-prediction model, and returns a
structured prediction.

> All data used by this project is synthetic and created for educational
> purposes. `Risk_Review_Flag` is a synthetic educational label, not a
> real fraud determination.

## Status

**Week 4 — final submission.** The full pipeline (ingestion,
validation, preprocessing, feature preparation, model, prediction,
output) is implemented and tested end to end, with a request/response
API on top that now has consistent error handling for every case:
invalid input (422), unknown customer (404), and any unexpected
failure (500, without leaking internals). No Data Science model was
ever received across Weeks 1–4 (solo on this track, confirmed again at
the start of Week 4), so the model stage runs ML Engineering's own
trained development model (`src/model/train.py`), honestly labelled as
such throughout. See `docs/risks.md` for final limitations,
`docs/week4-integration-note.md` for the cross-track status, and
`docs/week4-project-summary.md` for the full final report.

## Project structure

See `docs/architecture.md` for the full pipeline design and
`docs/technical-requirements.md` for input/output/preprocessing/testing
requirements.

```
fintrust-ml-engineering/
├── README.md
├── requirements.txt
├── .gitignore
├── docs/                   # Week 1-4 technical documentation
├── src/
│   ├── ingestion/          # Loads raw customer & transaction data
│   ├── validation/         # Schema / data-quality checks
│   ├── preprocessing/      # Missing-value handling, encoding, etc.
│   ├── features/           # Customer/transaction join + feature build
│   ├── model/              # Model interface + training script
│   ├── service/            # API layer (request/response prediction)
│   └── pipeline.py         # Orchestrates the full workflow
├── tests/                  # Automated tests, mirrors src/ structure
├── configs/                # Pipeline configuration (kept out of code)
├── data/                   # Raw CSVs (gitignored — see Reproducing below)
└── models/                 # Trained model artifacts (gitignored)
```

## Reproducing this project from a fresh clone

Another user should be able to go from a clean checkout to working
predictions with these five steps.

**1. Install dependencies**

```bash
python -m venv venv
venv\Scripts\activate        # Windows (use `source venv/bin/activate` on macOS/Linux)
pip install -r requirements.txt
```

**2. Prepare the data**

Place `FinTrust_Customer_Data.csv` and `FinTrust_Transaction_Data.csv`
(the approved FinTrust data resources) into a `data/` folder at the
repository root. This folder is gitignored, so it isn't part of the
repository itself — see `docs/risks.md` ("Static CSV input") and the
Week 1 version-control requirements for why.

**3. Run the workflow**

```bash
pytest tests/ -v                    # confirm everything passes first
python -m src.model.train           # trains and saves models/risk_review_model.pkl
python -m src.pipeline              # runs the full pipeline against data/
```

**4. Generate predictions via the API (optional)**

```bash
uvicorn src.service.api:app --reload
```

Then `POST` a transaction as JSON to `http://127.0.0.1:8000/predict`
(see `src/service/api.py` for the request/response shape), or `GET
/health` to confirm which model version is loaded. The API returns
`422` for invalid input, `404` for an unmatched `Customer_ID`, and a
generic `500` (no internal detail) for anything unexpected.

**5. Interpret the output**

Both the batch pipeline and the API return the same structure per
transaction: `Transaction_ID`, `Customer_ID`, `risk_review_prediction`
(0 or 1), `risk_review_probability` (0.0-1.0). A prediction of `1`
means the transaction is flagged for review by the current model —
this is a synthetic, educational signal, not a real fraud or risk
determination (see the disclaimer above and `docs/risks.md`).

If `models/risk_review_model.pkl` doesn't exist yet (step 3's training
command hasn't been run), the pipeline and API still work — they fall
back to the original placeholder rule and print a warning saying so,
rather than failing.

## Running tests

```bash
pytest tests/ -v
```

## Known limitations

- Uses static CSV snapshots (`FinTrust_Customer_Data.csv`,
  `FinTrust_Transaction_Data.csv`), not a live data source.
- The model is ML Engineering's own development model (trained on the
  real FinTrust data), not a Data Science deliverable — no Data
  Science model or interface was ever received across Weeks 1–4. See
  `docs/risks.md` and `docs/week4-project-summary.md` for its actual
  performance and final limitations.
- Intentional missing values exist in `Device_Type` and `Location`.
- `Risk_Review_Flag` is a synthetic, educational target and must never
  be represented as real fraud detection.
- This is a prototype, not a production banking system: no
  authentication on the API, no load testing, validated against one
  dataset snapshot only. See `docs/risks.md`'s final limitations and
  responsible-use statement.

## Further documentation

- `docs/architecture.md`, `docs/technical-requirements.md` — design
- `docs/testing-strategy.md`, `docs/week4-final-testing.md` — testing
- `docs/validation-refinement.md` — the Week 3 refinement log
- `docs/risks.md` — risk register, final limitations, responsible use
- `docs/week4-integration-note.md` — cross-track integration status
- `docs/week2-project-summary.md`, `docs/week3-project-summary.md`,
  `docs/week4-project-summary.md` — weekly project summaries
