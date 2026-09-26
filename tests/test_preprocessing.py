"""
Tests for src/preprocessing/preprocess.py.
"""

import pandas as pd
from src.preprocessing.preprocess import fill_missing, parse_datetime, encode_categoricals, preprocess


def _sample_df():
    return pd.DataFrame(
        {
            "Transaction_ID": ["FT-T000001", "FT-T000002"],
            "Customer_ID": ["FT-C00001", "FT-C00002"],
            "Transaction_DateTime": ["2026-01-01 00:00", "not-a-date"],
            "Transaction_Type": ["Card Purchase", "Transfer"],
            "Amount_NGN": [5923.80, 1000.00],
            "Channel": ["Mobile App", "ATM"],
            "Device_Type": ["Android", None],
            "Location": [None, "Kano"],
            "International_Transaction": ["No", "Yes"],
            "Transaction_Status": ["Reversed", "Successful"],
        }
    )


def test_fill_missing_replaces_device_type_and_location():
    df = _sample_df()
    result = fill_missing(df)
    assert result.loc[0, "Location"] == "Unknown"
    assert result.loc[1, "Device_Type"] == "Unknown"


def test_parse_datetime_converts_valid_values():
    df = _sample_df()
    result = parse_datetime(df)
    assert pd.api.types.is_datetime64_any_dtype(result["Transaction_DateTime"])


def test_parse_datetime_coerces_invalid_value_to_nat():
    df = _sample_df()
    result = parse_datetime(df)
    # row 1's "not-a-date" should become NaT rather than raise an error
    assert pd.isna(result.loc[1, "Transaction_DateTime"])


def test_encode_categoricals_produces_numeric_codes():
    df = _sample_df()
    result = encode_categoricals(df)
    assert pd.api.types.is_integer_dtype(result["Transaction_Type"])
    assert pd.api.types.is_integer_dtype(result["Channel"])


def test_preprocess_runs_full_sequence_without_error():
    df = _sample_df()
    result = preprocess(df)
    # By this point encode_categoricals has already run, so Location is a
    # numeric category code, not the literal string "Unknown" (that string
    # only exists briefly, between fill_missing and encode_categoricals —
    # see test_fill_missing_replaces_device_type_and_location for that check).
    # Here we just confirm the missing value was filled *and* encoded,
    # rather than left as a null/NaN code.
    assert pd.api.types.is_integer_dtype(result["Location"])
    assert result.loc[0, "Location"] != -1  # -1 is pandas' code for NaN/unfilled
    assert pd.api.types.is_datetime64_any_dtype(result["Transaction_DateTime"])
    assert pd.api.types.is_integer_dtype(result["Transaction_Type"])
