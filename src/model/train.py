"""
Trains and saves ML Engineering's own development classification
model for the FinTrust risk-review prediction.

Why this exists: Week 3's brief (Part C, Machine Learning Engineering
track) says to integrate a Data Science model where one is available,
and otherwise "use your own appropriate model... for development
purposes." No Data Science model was available (solo on this track),
so this script trains one. It is NOT a Data Science deliverable and
must not be represented as one, and Risk_Review_Flag remains a
synthetic, educational label, not a real fraud determination
(see docs/risks.md, the Week 1-3 briefs).

Data-leakage safeguard (docs/risks.md): Risk_Review_Flag is pulled out
of the transaction data and used ONLY as the training target, before
the same preprocess()/build_features() functions the live pipeline
uses are run. It never enters the feature set those functions produce,
on this path or the inference path.

Run:
    python -m src.model.train
"""

import os

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix,
)

from src.ingestion.data_loader import load_customer_data, load_transaction_data
from src.validation.schema_validator import validate_transaction_batch
from src.preprocessing.preprocess import preprocess
from src.features.feature_pipeline import join_customer_transaction

FEATURE_COLUMNS = [
    "Transaction_Type",
    "Amount_NGN",
    "Channel",
    "Device_Type",
    "Location",
    "International_Transaction",
    "Transaction_Status",
]

MODEL_VERSION = "mle-dev-logreg-0.1"


def _load_training_data(customer_path: str, transaction_path: str):
    customer_df = load_customer_data(customer_path)
    transaction_df = load_transaction_data(transaction_path)

    validation_result = validate_transaction_batch(transaction_df)
    if not validation_result.is_valid:
        raise ValueError(f"Training data failed validation: {validation_result.errors[:5]}")

    # Pull the target out BEFORE preprocessing/joining, on a separate
    # copy, so it never travels through the same functions the live
    # pipeline uses to build inference features.
    target = transaction_df[["Transaction_ID", "Risk_Review_Flag"]].copy()
    transaction_df = transaction_df.drop(columns=["Risk_Review_Flag"])

    processed_df = preprocess(transaction_df)
    joined = join_customer_transaction(customer_df, processed_df)
    joined = joined.merge(target, on="Transaction_ID", how="inner")

    y = (joined["Risk_Review_Flag"] == "Yes").astype(int)
    X = joined[FEATURE_COLUMNS]
    return X, y


def train(
    customer_path: str = "data/FinTrust_Customer_Data.csv",
    transaction_path: str = "data/FinTrust_Transaction_Data.csv",
    output_path: str = "models/risk_review_model.pkl",
) -> dict:
    X, y = _load_training_data(customer_path, transaction_path)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # class_weight="balanced" accounts for the ~80/20 class split
    # (about 19.6% Risk_Review_Flag = Yes in the real data) without
    # needing a separate resampling step.
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(
        {"model": model, "feature_columns": FEATURE_COLUMNS, "version": MODEL_VERSION},
        output_path,
    )

    return metrics


if __name__ == "__main__":
    result_metrics = train()
    print(f"Model saved. Trained on {result_metrics['train_rows']} rows, "
          f"tested on {result_metrics['test_rows']} rows.")
    print(f"Accuracy:  {result_metrics['accuracy']}")
    print(f"Precision: {result_metrics['precision']}")
    print(f"Recall:    {result_metrics['recall']}")
    print(f"F1:        {result_metrics['f1']}")
    print(f"Confusion matrix [[TN, FP], [FN, TP]]: {result_metrics['confusion_matrix']}")
