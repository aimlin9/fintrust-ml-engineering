"""
Tests for src/ingestion/data_loader.py.

Covers: a valid file loads correctly, a missing file raises
FileNotFoundError, and an empty file raises ValueError. Same pattern
for both load_customer_data and load_transaction_data.
"""

import pandas as pd
import pytest

from src.ingestion.data_loader import load_customer_data, load_transaction_data


def test_load_customer_data_reads_valid_file(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text("Customer_ID,Customer_Name\nFT-C00001,Ibrahim Adeyemi\n")

    result = load_customer_data(str(csv_path))

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1
    assert result.loc[0, "Customer_ID"] == "FT-C00001"


def test_load_customer_data_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_customer_data("does/not/exist.csv")


def test_load_customer_data_empty_file_raises(tmp_path):
    csv_path = tmp_path / "empty_customers.csv"
    csv_path.write_text("Customer_ID,Customer_Name\n")  # header only, no rows

    with pytest.raises(ValueError):
        load_customer_data(str(csv_path))


def test_load_transaction_data_reads_valid_file(tmp_path):
    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text(
        "Transaction_ID,Customer_ID,Amount_NGN\nFT-T000001,FT-C00001,5923.80\n"
    )

    result = load_transaction_data(str(csv_path))

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1
    assert result.loc[0, "Transaction_ID"] == "FT-T000001"


def test_load_transaction_data_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_transaction_data("does/not/exist.csv")


def test_load_transaction_data_empty_file_raises(tmp_path):
    csv_path = tmp_path / "empty_transactions.csv"
    csv_path.write_text("Transaction_ID,Customer_ID,Amount_NGN\n")  # header only

    with pytest.raises(ValueError):
        load_transaction_data(str(csv_path))
