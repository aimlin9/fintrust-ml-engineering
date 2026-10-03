"""
Tests for src/service/api.py. Uses FastAPI's TestClient, which drives
the app directly in-process — no need to run uvicorn for these tests.

These tests inject the known placeholder RiskModel (rather than
whatever happens to be at configs/pipeline_config.yaml's model.path)
so assertions stay deterministic and don't depend on a trained model
file existing, or on that model's coefficients after a future
retraining run. Confirming the API uses the REAL trained model when
one is present is covered separately in test_model_interface.py
(test_load_model_loads_trained_model_file_when_present) and by
docs/testing-strategy.md's end-to-end run.
"""

import pytest
from fastapi.testclient import TestClient

from src.service import api
from src.model.model_interface import RiskModel

client = TestClient(api.app)


@pytest.fixture(autouse=True)
def _use_throwaway_customer_table_and_mock_model(tmp_path, monkeypatch):
    """
    Point the API at a small, temporary customer table for each test,
    instead of the real data/ CSV (which is gitignored and may not
    exist on every machine that runs the tests), and inject the known
    placeholder model so prediction assertions are deterministic.
    """
    customer_csv = tmp_path / "customers.csv"
    customer_csv.write_text(
        "Customer_ID,Customer_Name,Age\n"
        "FT-C00001,Ibrahim Adeyemi,56\n"
    )
    monkeypatch.setattr(api, "_CUSTOMER_DATA_PATH", str(customer_csv))
    monkeypatch.setattr(api, "_customer_df", None)
    monkeypatch.setattr(api, "_model", RiskModel(model_version="mock-0.1"))


def _valid_transaction(**overrides):
    row = {
        "Transaction_ID": "FT-T000001",
        "Customer_ID": "FT-C00001",
        "Transaction_DateTime": "2026-01-01 00:00",
        "Transaction_Type": "Card Purchase",
        "Amount_NGN": 75000.0,
        "Channel": "Mobile App",
        "Device_Type": "Android",
        "Location": "Enugu",
        "International_Transaction": "Yes",
        "Transaction_Status": "Reversed",
    }
    row.update(overrides)
    return row


def test_health_endpoint_returns_model_version():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["model_version"] == "mock-0.1"


def test_predict_valid_transaction_returns_prediction():
    response = client.post("/predict", json=_valid_transaction())

    assert response.status_code == 200
    body = response.json()
    assert body["Transaction_ID"] == "FT-T000001"
    assert body["Customer_ID"] == "FT-C00001"
    # Amount_NGN > 50000 and International_Transaction == "Yes" -> both
    # score bumps apply, same math as test_model_interface.py.
    assert body["risk_review_prediction"] == 1
    assert body["risk_review_probability"] == pytest.approx(0.6)


def test_predict_small_domestic_transaction_scores_low():
    row = _valid_transaction(Amount_NGN=500.0, International_Transaction="No")
    response = client.post("/predict", json=row)

    assert response.status_code == 200
    body = response.json()
    assert body["risk_review_prediction"] == 0
    assert body["risk_review_probability"] == pytest.approx(0.1)


def test_predict_missing_required_field_returns_422():
    row = _valid_transaction()
    del row["Transaction_DateTime"]

    response = client.post("/predict", json=row)

    # Pydantic itself rejects the missing required field before our
    # business validation ever runs.
    assert response.status_code == 422


def test_predict_unexpected_category_returns_422():
    row = _valid_transaction(International_Transaction="Maybe")

    response = client.post("/predict", json=row)

    assert response.status_code == 422


def test_predict_unknown_customer_returns_404():
    row = _valid_transaction(Customer_ID="FT-C99999")

    response = client.post("/predict", json=row)

    assert response.status_code == 404
