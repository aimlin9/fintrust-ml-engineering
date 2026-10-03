"""
Service stage — request/response prediction service: a single
transaction in, a risk-review prediction out.

Reuses the same validation, preprocessing, feature-joining, and model
stages as pipeline.py (the batch path) so there is one source of truth
for each piece of logic. As of Week 3, preprocessing (including
categorical encoding) uses the same fixed, config-driven mapping for
both the batch pipeline and this API — see
src/preprocessing/preprocess.py::encode_categoricals for why that
matters and what it replaced.

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
from src.preprocessing.preprocess import preprocess
from src.features.feature_pipeline import build_features
from src.model.model_interface import load_model

app = FastAPI(
    title="FinTrust Risk Review API",
    description="Single-transaction risk-review prediction service.",
    version="0.2.0",
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


@app.post("/predict", response_model=PredictionResponse)
def predict(transaction: TransactionRequest):
    row = transaction.model_dump()

    validation_result = validate_transaction_row(row)
    if not validation_result.is_valid:
        raise HTTPException(status_code=422, detail=validation_result.errors)

    # Same preprocess() sequence as the batch pipeline (fill_missing ->
    # parse_datetime -> encode_categoricals), so a single request is
    # preprocessed identically to a row inside a full-CSV batch.
    transaction_df = preprocess(pd.DataFrame([row]))

    customer_df = _get_customer_df()
    features_df = build_features(customer_df, transaction_df)
    if features_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Customer_ID {row['Customer_ID']} not found in customer records",
        )

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
