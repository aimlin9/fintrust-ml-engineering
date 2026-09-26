"""
Preprocessing stage — cleans and standardises records that passed
validation: fills known missing values, parses datetimes, and encodes
categorical fields.
"""

import os
import yaml
import pandas as pd


def _load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "pipeline_config.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    config = _load_config()
    defaults = config.get("missing_value_defaults", {})
    for col, default in defaults.items():
        if col in df.columns:
            df[col] = df[col].fillna(default)
    return df


def parse_datetime(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Transaction_DateTime" in df.columns:
        df["Transaction_DateTime"] = pd.to_datetime(df["Transaction_DateTime"], errors="coerce")
    return df


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    categorical_cols = [
        "Transaction_Type",
        "Channel",
        "Device_Type",
        "Location",
        "International_Transaction",
        "Transaction_Status",
    ]
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype("category").cat.codes
    return df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = fill_missing(df)
    df = parse_datetime(df)
    df = encode_categoricals(df)
    return df
