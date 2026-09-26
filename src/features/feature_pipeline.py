"""
Feature Preparation stage — joins customer + transaction data and
builds the final feature set for the model.
"""

import pandas as pd

MODEL_FIELDS = [
    "Transaction_ID",
    "Customer_ID",
    "Transaction_DateTime",
    "Transaction_Type",
    "Amount_NGN",
    "Channel",
    "Device_Type",
    "Location",
    "International_Transaction",
    "Transaction_Status",
]


def join_customer_transaction(customer_df: pd.DataFrame, transaction_df: pd.DataFrame) -> pd.DataFrame:
    merged = transaction_df.merge(customer_df, on="Customer_ID", how="left", indicator=True)
    unmatched = merged[merged["_merge"] == "left_only"]
    if not unmatched.empty:
        # Unmatched Customer_ID — documented risk (docs/risks.md). Excluded rather
        # than silently included with missing customer fields.
        print(f"Warning: {len(unmatched)} transaction(s) have no matching customer record and were excluded.")
    matched = merged[merged["_merge"] == "both"].drop(columns=["_merge"])
    return matched


def select_model_fields(df: pd.DataFrame) -> pd.DataFrame:
    available = [f for f in MODEL_FIELDS if f in df.columns]
    return df[available]


def build_features(customer_df: pd.DataFrame, transaction_df: pd.DataFrame) -> pd.DataFrame:
    joined = join_customer_transaction(customer_df, transaction_df)
    return select_model_fields(joined)
