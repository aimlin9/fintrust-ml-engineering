"""
Service stage — optional advanced component (Week 2 brief). Exposes
the pipeline as a request/response prediction service: a single
transaction in, a risk-review prediction out.

Reuses the same validation, feature-joining, and model stages as
pipeline.py (the batch path) so there is one source of truth for each
piece of logic. The one deliberate divergence — single-row categorical
encoding — is explained in _encode_single_transaction() below.

Run locally with:
    uvicorn src.service.api:app --reload
Then POST a transaction to http://127.0.0.1:8000/predict
"""

import os

import pandas as pd
import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.validation.schema_validator import validate_transaction_row
from src.ingestion.data_loader import load_customer_data
from src.preprocessing.preprocess import fill_missing
from src.features.feature_pipeline import join_customer_transaction, select_model_fields
from src.model.model_interface import load_model

app = FastAPI(
    title="FinTrust Risk Review API",
    description="Optional Week 2 service concept — single-transaction risk-review prediction.",
    version="0.1.0",
)

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "pipeline_config.yaml")
_CUSTOMER_DATA_PATH = os.environ.get(
    "FINTRUST_CUSTOMER_DATA_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "FinTrust_Customer_Data.csv"),
)

# Lazily loaded and cached so a request doesn't re-read the config/CSV
# every time. Tests override these via monkeypatch (see tests/test_api.py).
_model = None
_customer_df = None


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _get_model():
    global _model
    if _model is None:
        _model = load_model(_load_config())
    return _model


def _get_customer_df() -> pd.DataFrame:
    global _customer_df
    if _customer_df is None:
        _customer_df = load_customer_data(_CUSTOMER_DATA_PATH)
    return _customer_df


class TransactionRequest(BaseModel):
    Transaction_ID: str
    Customer_ID: str
    Transaction_DateTime: str
    Transaction_Type: str
    Amount_NGN: float
    Channel: str
    Device_Type: Optional[str] = None
    Location: Optional[str] = None
    International_Transaction: str
    Transaction_Status: str


class PredictionResponse(BaseModel):
    Transaction_ID: str
    Customer_ID: str
    risk_review_prediction: int
    risk_review_probability: float


def _encode_single_transaction(row: dict) -> dict:
    """
    Deterministic, row-level encoding for a single transaction.

    KNOWN LIMITATION (documented decision, not an oversight): the batch
    pipeline's encode_categoricals() (src/preprocessing/preprocess.py)
    encodes each column with pandas' `.cat.codes`, which assigns codes
    relative to whatever categories are present in that specific batch.
    That's fine when scoring a full CSV (pipeline.py), but it is NOT
    safe for a single-row API request: a lone "Yes" or "No" value would
    always encode to category code 0, since there's only one category
    in a "batch" of one row. Left as-is, the mock model's
    International_Transaction check would never fire for a real-time
    request.

    Real fix (Week 3+, once Data Science's category scheme is final):
    agree a fixed category-to-code mapping and load it from config, so
    the batch pipeline and this API always encode the same value the
    same way. Until then, this function hardcodes the one mapping the
    mock model actually depends on, so this endpoint is correct today
    without pretending the underlying encoding approach is finished.
    """
    encoded = dict(row)
    encoded["International_Transaction"] = 1 if row.get("International_Transaction") == "Yes" else 0
    return encoded


@app.post("/predict", response_model=PredictionResponse)
def predict(transaction: TransactionRequest):
    row = transaction.model_dump()

    validation_result = validate_transaction_row(row)
    if not validation_result.is_valid:
        raise HTTPException(status_code=422, detail=validation_result.errors)

    transaction_df = fill_missing(pd.DataFrame([row]))

    customer_df = _get_customer_df()
    joined = join_customer_transaction(customer_df, transaction_df)
    if joined.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Customer_ID {row['Customer_ID']} not found in customer records",
        )

    encoded_row = _encode_single_transaction(joined.iloc[0].to_dict())
    features_df = select_model_fields(pd.DataFrame([encoded_row]))

    model = _get_model()
    prediction_df = model.predict(features_df)

    return PredictionResponse(
        Transaction_ID=row["Transaction_ID"],
        Customer_ID=row["Customer_ID"],
        risk_review_prediction=int(prediction_df.loc[0, "risk_review_prediction"]),
        risk_review_probability=float(prediction_df.loc[0, "risk_review_probability"]),
    )


@app.get("/health")
def health():
    return {"status": "ok", "model_version": _get_model().model_version}
