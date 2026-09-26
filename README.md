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

Week 2 — initial implementation of the pipeline skeleton (ingestion,
validation, preprocessing, prediction workflow) with a mock model
interface, pending the trained model artifact from the Data Science
track.

## Project structure

See `docs/architecture.md` for the full pipeline design and
`docs/technical-requirements.md` for input/output/preprocessing/testing
requirements.

```
fintrust-ml-engineering/
├── README.md
├── requirements.txt
├── .gitignore
├── docs/                   # Week 1 + Week 2 technical documentation
├── src/
│   ├── ingestion/          # Loads raw customer & transaction data
│   ├── validation/         # Schema / data-quality checks
│   ├── preprocessing/      # Missing-value handling, encoding, etc.
│   ├── features/           # Customer/transaction join + feature build
│   ├── model/              # Model interface (mock until DS delivers one)
│   ├── service/            # API layer (request/response prediction)
│   └── pipeline.py         # Orchestrates the full workflow
├── tests/                  # Automated tests, mirrors src/ structure
└── configs/                # Pipeline configuration (kept out of code)
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Running tests

```bash
pytest tests/
```

## Known limitations

- Uses static CSV snapshots (`FinTrust_Customer_Data.csv`,
  `FinTrust_Transaction_Data.csv`), not a live data source.
- The model stage uses a mock interface pending a trained model artifact
  from the Data Science track (see `docs/risks.md`).
- Intentional missing values exist in `Device_Type` and `Location`.
