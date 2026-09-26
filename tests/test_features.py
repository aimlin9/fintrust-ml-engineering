"""
Tests for src/features/feature_pipeline.py — including the unmatched
Customer_ID case (docs/risks.md).
"""

import pandas as pd
from src.features.feature_pipeline import join_customer_transaction, select_model_fields, build_features


def _customer_df():
    return pd.DataFrame(
        {
            "Customer_ID": ["FT-C00001", "FT-C00002"],
            "Customer_Name": ["Ibrahim Adeyemi", "Yusuf Mohammed"],
            "Age": [56, 46],
        }
    )


def _transaction_df():
    return pd.DataFrame(
        {
            "Transaction_ID": ["FT-T000001", "FT-T000002"],
            "Customer_ID": ["FT-C00001", "FT-C99999"],  # second has no matching customer
            "Transaction_DateTime": ["2026-01-01 00:00", "2026-01-01 00:10"],
            "Transaction_Type": ["Card Purchase", "Cash Withdrawal"],
            "Amount_NGN": [5923.80, 11681.12],
            "Channel": ["Mobile App", "ATM"],
            "Device_Type": ["Android", "Android"],
            "Location": ["Enugu", "Kaduna"],
            "International_Transaction": ["No", "No"],
            "Transaction_Status": ["Reversed", "Successful"],
        }
    )


def test_join_excludes_unmatched_customer_id():
    result = join_customer_transaction(_customer_df(), _transaction_df())
    # Only the transaction with a matching Customer_ID should remain
    assert len(result) == 1
    assert result.iloc[0]["Transaction_ID"] == "FT-T000001"


def test_select_model_fields_excludes_non_modelling_columns():
    joined = join_customer_transaction(_customer_df(), _transaction_df())
    result = select_model_fields(joined)
    # Customer_Name is Modelling_Use: No in the data dictionary — must not appear
    assert "Customer_Name" not in result.columns
    assert "Transaction_ID" in result.columns
    assert "Amount_NGN" in result.columns


def test_build_features_end_to_end():
    result = build_features(_customer_df(), _transaction_df())
    assert len(result) == 1
    assert "Customer_Name" not in result.columns
