"""
Ingestion stage — loads the raw FinTrust customer and transaction
records into the pipeline. Does not validate or clean data; that
happens in validation/ and preprocessing/.
"""

import os
import pandas as pd


def load_customer_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Customer data file not found: {path}")
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(f"Customer data file is empty: {path}")
    return df


def load_transaction_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Transaction data file not found: {path}")
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(f"Transaction data file is empty: {path}")
    return df
