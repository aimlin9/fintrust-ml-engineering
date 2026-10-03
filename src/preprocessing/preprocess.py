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
    """
    Encodes categorical fields using the fixed category -> code mapping
    in configs/pipeline_config.yaml (categorical_encodings).

    Week 3 change: this used to call pandas' `.astype("category").cat.codes`,
    which assigns codes relative to whichever categories are present in
    the DataFrame being encoded. That's fine for a full-CSV batch, but
    it silently breaks for a single-row request (e.g. the API) — a lone
    "Yes" has nothing else to be relative to, so it always encoded to 0.
    Using one fixed mapping for both the batch pipeline and the API
    closes that gap: the same value always encodes to the same code,
    regardless of batch size. A value not present in the mapping (not
    seen in the data this mapping was built from) encodes to -1 rather
    than silently colliding with a real code, so it stays visible as a
    data-quality case rather than quietly corrupting a feature.
    """
    df = df.copy()
    config = _load_config()
    encodings = config.get("categorical_encodings", {})
    for col, mapping in encodings.items():
        if col in df.columns:
            df[col] = df[col].map(mapping).fillna(-1).astype(int)
    return df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = fill_missing(df)
    df = parse_datetime(df)
    df = encode_categoricals(df)
    return df
