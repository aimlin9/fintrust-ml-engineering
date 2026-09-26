"""
Model stage — the interface between ML Engineering and the Data
Science track's model. The real trained model isn't available yet
(see docs/risks.md), so this defines a MOCK model with the same
contract a real one would have: it takes prepared features and
returns a prediction + probability per row.

When Data Science delivers a real model, only this file should need
to change.
"""

import pandas as pd


class RiskModel:
    def __init__(self, model_version: str = "mock-0.1"):
        self.model_version = model_version

    def predict(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Placeholder scoring logic only — NOT a trained model. Exists to
        prove the pipeline is wired together end to end. Flags larger
        and international transactions as somewhat higher risk, which
        is a reasonable-looking but entirely made-up rule.
        """
        probabilities = []
        for _, row in features_df.iterrows():
            score = 0.1
            amount = row.get("Amount_NGN")
            if pd.notna(amount) and amount > 50000:
                score += 0.3
            # International_Transaction is encoded (0/1) by preprocessing;
            # after encode_categoricals, "Yes" and "No" become category codes.
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


def load_model(config: dict) -> RiskModel:
    model_version = config.get("model", {}).get("version", "mock-0.1")
    return RiskModel(model_version=model_version)
