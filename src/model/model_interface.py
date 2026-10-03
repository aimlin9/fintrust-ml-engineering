"""
Model stage — the interface between the rest of the pipeline and
whatever model is actually scoring transactions.

Week 3 change: no Data Science model was available to integrate (solo
on this track — see docs/risks.md, "Dependency on Data Science
track"). Per the Week 3 brief (Part C, ML Engineering), that means
using "your own appropriate model... for development purposes," so
TrainedRiskModel wraps a real classifier trained on the actual
FinTrust data (src/model/train.py), instead of the Week 2 placeholder
rule. This model is ML Engineering's own development model. It is NOT
a Data Science deliverable, and Risk_Review_Flag remains a synthetic,
educational label, not a real fraud determination.

load_model() loads the trained model from configs/pipeline_config.yaml's
model.path if that file exists, and falls back to the original mock
(RiskModel) with a clear warning if it doesn't — e.g. on a fresh clone
before anyone has run `python -m src.model.train`. Both classes share
the same predict() contract, so pipeline.py and api.py don't need to
know or care which one is in use.

When Data Science delivers a real model, only this file (and
train.py, if it's superseded entirely) should need to change.
"""

import os

import joblib
import pandas as pd


class RiskModel:
    """Placeholder scoring logic only — NOT a trained model. Kept as
    the fallback for when no trained model file exists yet."""

    def __init__(self, model_version: str = "mock-0.1"):
        self.model_version = model_version

    def predict(self, features_df: pd.DataFrame) -> pd.DataFrame:
        probabilities = []
        for _, row in features_df.iterrows():
            score = 0.1
            amount = row.get("Amount_NGN")
            if pd.notna(amount) and amount > 50000:
                score += 0.3
            if row.get("International_Transaction") == 1:
                score += 0.2
            probabilities.append(min(score, 0.95))

        predictions = [1 if p >= 0.5 else 0 for p in probabilities]

        return pd.DataFrame(
            {
                "risk_review_prediction": predictions,
                "risk_review_probability": probabilities,
            }
        )


class TrainedRiskModel:
    """
    Wraps a scikit-learn classifier trained by src/model/train.py.

    Loaded from a joblib file containing {"model", "feature_columns",
    "version"} (see train.py). feature_columns fixes the exact column
    order/selection the model was trained on, so predict() always
    hands the model the same shape it saw during training regardless
    of what extra columns features_df happens to carry (e.g.
    Transaction_ID, Transaction_DateTime).
    """

    def __init__(self, model, feature_columns: list, model_version: str):
        self._model = model
        self._feature_columns = feature_columns
        self.model_version = model_version

    def predict(self, features_df: pd.DataFrame) -> pd.DataFrame:
        X = features_df[self._feature_columns]
        probabilities = self._model.predict_proba(X)[:, 1]
        predictions = self._model.predict(X)

        return pd.DataFrame(
            {
                "risk_review_prediction": predictions.astype(int),
                "risk_review_probability": probabilities,
            }
        )

    @classmethod
    def from_file(cls, path: str) -> "TrainedRiskModel":
        bundle = joblib.load(path)
        return cls(
            model=bundle["model"],
            feature_columns=bundle["feature_columns"],
            model_version=bundle["version"],
        )


def load_model(config: dict):
    model_config = config.get("model", {})
    model_version = model_config.get("version", "mock-0.1")
    model_path = model_config.get("path")

    if model_path and os.path.exists(model_path):
        return TrainedRiskModel.from_file(model_path)

    print(
        f"Warning: no trained model found at {model_path!r} — falling back to the "
        "placeholder RiskModel. Run `python -m src.model.train` to train and save "
        "a real development model."
    )
    return RiskModel(model_version=model_version)
