"""
Tests for src/model/model_interface.py.

Covers both models behind the shared predict() contract:
- RiskModel, the placeholder rule (kept as the fallback when no
  trained model file exists) — these tests confirm the interface
  contract and the rule's documented behaviour, not that it is
  "correct" in any trained sense.
- TrainedRiskModel, which wraps a real scikit-learn classifier trained
  by src/model/train.py (Week 3) — and load_model()'s choice between
  the two based on whether a trained model file is present.
"""

import joblib
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.model.model_interface import RiskModel, TrainedRiskModel, load_model


def _features_df(rows):
    return pd.DataFrame(rows)


def test_predict_returns_one_prediction_and_probability_per_row():
    model = RiskModel()
    features_df = _features_df(
        [
            {"Amount_NGN": 1000.0, "International_Transaction": 0},
            {"Amount_NGN": 2000.0, "International_Transaction": 1},
        ]
    )

    result = model.predict(features_df)

    assert list(result.columns) == ["risk_review_prediction", "risk_review_probability"]
    assert len(result) == len(features_df)


def test_predict_flags_large_international_transaction_as_higher_risk():
    model = RiskModel()
    # Amount_NGN > 50000 and International_Transaction == 1 (encoded "Yes")
    # should stack both score bumps: 0.1 base + 0.3 + 0.2 = 0.6 -> prediction 1
    features_df = _features_df([{"Amount_NGN": 75000.0, "International_Transaction": 1}])

    result = model.predict(features_df)

    # pytest.approx guards against binary floating-point rounding: 0.1 + 0.3
    # + 0.2 evaluates to 0.6000000000000001 in Python, not exactly 0.6.
    assert result.loc[0, "risk_review_probability"] == pytest.approx(0.6)
    assert result.loc[0, "risk_review_prediction"] == 1


def test_predict_small_domestic_transaction_scores_low():
    model = RiskModel()
    # Neither condition triggers: score stays at the 0.1 base -> prediction 0
    features_df = _features_df([{"Amount_NGN": 500.0, "International_Transaction": 0}])

    result = model.predict(features_df)

    assert result.loc[0, "risk_review_probability"] == 0.1
    assert result.loc[0, "risk_review_prediction"] == 0


def test_predict_caps_probability_at_point_nine_five():
    model = RiskModel()
    # Even with every bump applied the score should never exceed 0.95
    features_df = _features_df([{"Amount_NGN": 1_000_000.0, "International_Transaction": 1}])

    result = model.predict(features_df)

    assert result.loc[0, "risk_review_probability"] <= 0.95


def test_predict_handles_missing_amount_without_error():
    model = RiskModel()
    features_df = _features_df([{"Amount_NGN": None, "International_Transaction": 0}])

    # Should not raise — pd.notna() guards the amount check
    result = model.predict(features_df)

    assert len(result) == 1


def test_load_model_uses_version_from_config():
    config = {"model": {"version": "mock-0.1"}}
    model = load_model(config)

    assert isinstance(model, RiskModel)
    assert model.model_version == "mock-0.1"


def test_load_model_defaults_when_version_missing():
    model = load_model({})

    assert model.model_version == "mock-0.1"


# ---------------------------------------------------------------------
# TrainedRiskModel / load_model's trained-vs-mock fallback (Week 3)
# ---------------------------------------------------------------------

def _tiny_trained_bundle(tmp_path):
    """
    A small, fast, fully-deterministic trained model bundle — not meant
    to be a good classifier, just a real one with the exact shape
    TrainedRiskModel expects, for testing model LOADING and the
    predict() contract rather than model quality.
    """
    feature_columns = ["Transaction_Type", "Amount_NGN", "International_Transaction"]
    X = pd.DataFrame(
        {
            "Transaction_Type": [0, 1, 2, 3, 4, 5, 0, 1],
            "Amount_NGN": [100.0, 200.0, 90000.0, 80000.0, 150.0, 120.0, 95000.0, 110.0],
            "International_Transaction": [0, 0, 1, 1, 0, 0, 1, 0],
        }
    )
    y = [0, 0, 1, 1, 0, 0, 1, 0]

    model = LogisticRegression()
    model.fit(X, y)

    bundle_path = tmp_path / "tiny_model.pkl"
    joblib.dump({"model": model, "feature_columns": feature_columns, "version": "test-tiny-0.1"}, bundle_path)
    return str(bundle_path), feature_columns


def test_trained_risk_model_from_file_loads_and_predicts(tmp_path):
    bundle_path, feature_columns = _tiny_trained_bundle(tmp_path)

    model = TrainedRiskModel.from_file(bundle_path)
    features_df = pd.DataFrame(
        [{"Transaction_Type": 2, "Amount_NGN": 90000.0, "International_Transaction": 1}]
    )

    result = model.predict(features_df)

    # Same output contract as RiskModel: exactly these two columns.
    assert list(result.columns) == ["risk_review_prediction", "risk_review_probability"]
    assert len(result) == 1
    assert result.loc[0, "risk_review_prediction"] in (0, 1)
    assert 0.0 <= result.loc[0, "risk_review_probability"] <= 1.0
    assert model.model_version == "test-tiny-0.1"


def test_trained_risk_model_ignores_extra_columns(tmp_path):
    """
    features_df coming out of the pipeline carries Transaction_ID,
    Customer_ID, Transaction_DateTime etc. alongside the model's actual
    feature columns. predict() must select only feature_columns, not
    choke on or accidentally use the extras.
    """
    bundle_path, _ = _tiny_trained_bundle(tmp_path)
    model = TrainedRiskModel.from_file(bundle_path)

    features_df = pd.DataFrame(
        [{
            "Transaction_ID": "FT-T000001",
            "Customer_ID": "FT-C00001",
            "Transaction_Type": 2,
            "Amount_NGN": 90000.0,
            "International_Transaction": 1,
        }]
    )

    result = model.predict(features_df)
    assert len(result) == 1


def test_load_model_loads_trained_model_file_when_present(tmp_path):
    bundle_path, _ = _tiny_trained_bundle(tmp_path)
    config = {"model": {"version": "ignored-when-path-is-set", "path": bundle_path}}

    model = load_model(config)

    assert isinstance(model, TrainedRiskModel)
    assert model.model_version == "test-tiny-0.1"


def test_load_model_falls_back_to_mock_when_file_missing(tmp_path, capsys):
    missing_path = str(tmp_path / "does_not_exist.pkl")
    config = {"model": {"version": "mock-0.1", "path": missing_path}}

    model = load_model(config)

    assert isinstance(model, RiskModel)
    assert "Warning" in capsys.readouterr().out
