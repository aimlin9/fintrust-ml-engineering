"""
Tests for src/model/model_interface.py.

This is a MOCK model (see the module's own docstring) — these tests
confirm the interface contract (one prediction + one probability per
row) and the placeholder scoring rule behave as documented, not that
the model is "correct" in any trained sense.
"""

import pandas as pd
import pytest

from src.model.model_interface import RiskModel, load_model


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
