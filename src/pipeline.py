"""
Pipeline orchestrator — ties every stage together in order:
Data -> Validation -> Preprocessing -> Feature Preparation -> Model
-> Prediction -> Output
"""

import os
import yaml
import pandas as pd

from src.ingestion.data_loader import load_customer_data, load_transaction_data
from src.validation.schema_validator import validate_transaction_batch
from src.preprocessing.preprocess import preprocess
from src.features.feature_pipeline import build_features
from src.model.model_interface import load_model


def _load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "..", "configs", "pipeline_config.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_pipeline(customer_path: str, transaction_path: str) -> dict:
    customer_df = load_customer_data(customer_path)
    transaction_df = load_transaction_data(transaction_path)

    validation_result = validate_transaction_batch(transaction_df)
    if not validation_result.is_valid:
        # Decision: invalid records stop the batch here and are reported
        # back as errors, rather than silently dropped or partially
        # processed. See docs/technical-requirements.md.
        return {"predictions": [], "errors": validation_result.errors}

    processed_df = preprocess(transaction_df)
    features_df = build_features(customer_df, processed_df)

    config = _load_config()
    model = load_model(config)
    predictions_df = model.predict(features_df)

    output_df = pd.concat(
        [features_df[["Transaction_ID", "Customer_ID"]].reset_index(drop=True), predictions_df],
        axis=1,
    )
    return {"predictions": output_df.to_dict(orient="records"), "errors": []}


if __name__ == "__main__":
    result = run_pipeline(
        "data/FinTrust_Customer_Data.csv",
        "data/FinTrust_Transaction_Data.csv",
    )
    print(result)
