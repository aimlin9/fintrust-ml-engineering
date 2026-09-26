"""
Tests for src/validation/schema_validator.py.

Covers the five test types the Week 2 brief asks for: valid input,
missing values, unexpected category, incorrect data type, empty input.
"""

import pandas as pd
from src.validation.schema_validator import validate_transaction_row, validate_transaction_batch


def test_valid_transaction_passes():
    row = {
        "Transaction_ID": "FT-T000001",
        "Customer_ID": "FT-C00001",
        "Transaction_DateTime": "2026-01-01 00:00",
        "Transaction_Type": "Card Purchase",
        "Amount_NGN": 5923.80,
        "Channel": "Mobile App",
        "Device_Type": "Android",
        "Location": "Enugu",
        "International_Transaction": "No",
        "Transaction_Status": "Reversed",
    }
    result = validate_transaction_row(row)
    assert result.is_valid
    assert result.errors == []


def test_missing_required_field_fails():
    row = {
        "Transaction_ID": "FT-T000002",
        "Customer_ID": "FT-C00002",
        # Transaction_DateTime missing
        "Transaction_Type": "Transfer",
        "Amount_NGN": 1000,
        "Channel": "ATM",
        "International_Transaction": "No",
        "Transaction_Status": "Successful",
    }
    result = validate_transaction_row(row)
    assert not result.is_valid
    assert any("Transaction_DateTime" in e for e in result.errors)


def test_unexpected_category_fails():
    row = {
        "Transaction_ID": "FT-T000003",
        "Customer_ID": "FT-C00003",
        "Transaction_DateTime": "2026-01-01 00:21",
        "Transaction_Type": "Transfer",
        "Amount_NGN": 571.91,
        "Channel": "ATM",
        "International_Transaction": "Maybe",  # not "Yes" or "No"
        "Transaction_Status": "Successful",
    }
    result = validate_transaction_row(row)
    assert not result.is_valid
    assert any("International_Transaction" in e for e in result.errors)


def test_incorrect_data_type_fails():
    row = {
        "Transaction_ID": "FT-T000004",
        "Customer_ID": "FT-C00004",
        "Transaction_DateTime": "2026-01-01 00:32",
        "Transaction_Type": "Deposit",
        "Amount_NGN": "not-a-number",
        "Channel": "Mobile App",
        "International_Transaction": "No",
        "Transaction_Status": "Successful",
    }
    result = validate_transaction_row(row)
    assert not result.is_valid
    assert any("Amount_NGN" in e for e in result.errors)


def test_empty_input_handled_cleanly():
    empty_df = pd.DataFrame()
    result = validate_transaction_batch(empty_df)
    assert not result.is_valid
    assert "empty" in result.errors[0].lower()
