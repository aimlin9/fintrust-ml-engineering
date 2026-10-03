"""
Tests for src/pipeline.py — the orchestrator itself.

Week 2 tested every stage in isolation but never pipeline.py's own
logic (stitching the stages together, the early-return-on-invalid-batch
decision). Week 3's brief (Part D) also explicitly asks for output
format and reproducibility to be tested, on top of the existing
valid/missing/unexpected-category/invalid-type/empty-input cases — this
file covers all three at the pipeline level, using small on-disk CSVs
rather than the full FinTrust data so these tests stay fast and
self-contained.
"""

import pandas as pd
import pytest

from src.pipeline import run_pipeline


def _write_customer_csv(path):
    path.write_text(
        "Customer_ID,Customer_Name,Age\n"
        "FT-C00001,Ibrahim Adeyemi,56\n"
        "FT-C00002,Yusuf Mohammed,46\n"
    )


def _write_valid_transaction_csv(path):
    path.write_text(
        "Transaction_ID,Customer_ID,Transaction_DateTime,Transaction_Type,"
        "Amount_NGN,Channel,Device_Type,Location,International_Transaction,"
        "Transaction_Status\n"
        "FT-T000001,FT-C00001,2026-01-01 00:00,Card Purchase,75000.0,"
        "Mobile App,Android,Enugu,Yes,Reversed\n"
        "FT-T000002,FT-C00002,2026-01-01 00:10,Cash Withdrawal,500.0,"
        "ATM,Android,Kaduna,No,Successful\n"
    )


def _write_invalid_transaction_csv(path):
    # International_Transaction has an unexpected category ("Maybe"),
    # which validate_transaction_batch should catch.
    path.write_text(
        "Transaction_ID,Customer_ID,Transaction_DateTime,Transaction_Type,"
        "Amount_NGN,Channel,Device_Type,Location,International_Transaction,"
        "Transaction_Status\n"
        "FT-T000001,FT-C00001,2026-01-01 00:00,Card Purchase,75000.0,"
        "Mobile App,Android,Enugu,Maybe,Reversed\n"
    )


def test_run_pipeline_output_format(tmp_path):
    customer_csv = tmp_path / "customers.csv"
    transaction_csv = tmp_path / "transactions.csv"
    _write_customer_csv(customer_csv)
    _write_valid_transaction_csv(transaction_csv)

    result = run_pipeline(str(customer_csv), str(transaction_csv))

    assert result["errors"] == []
    assert len(result["predictions"]) == 2
    for row in result["predictions"]:
        assert set(row.keys()) == {
            "Transaction_ID", "Customer_ID",
            "risk_review_prediction", "risk_review_probability",
        }
        assert row["risk_review_prediction"] in (0, 1)
        assert 0.0 <= row["risk_review_probability"] <= 1.0


def test_run_pipeline_is_reproducible(tmp_path):
    customer_csv = tmp_path / "customers.csv"
    transaction_csv = tmp_path / "transactions.csv"
    _write_customer_csv(customer_csv)
    _write_valid_transaction_csv(transaction_csv)

    first_run = run_pipeline(str(customer_csv), str(transaction_csv))
    second_run = run_pipeline(str(customer_csv), str(transaction_csv))

    assert first_run == second_run


def test_run_pipeline_returns_errors_for_invalid_batch_without_crashing(tmp_path):
    customer_csv = tmp_path / "customers.csv"
    transaction_csv = tmp_path / "transactions.csv"
    _write_customer_csv(customer_csv)
    _write_invalid_transaction_csv(transaction_csv)

    result = run_pipeline(str(customer_csv), str(transaction_csv))

    assert result["predictions"] == []
    assert len(result["errors"]) > 0
    assert any("International_Transaction" in e for e in result["errors"])
