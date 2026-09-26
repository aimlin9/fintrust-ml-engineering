"""
Validation stage — checks incoming transaction records against the
expected schema before anything else touches them.
"""

from dataclasses import dataclass, field
import pandas as pd


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list = field(default_factory=list)


REQUIRED_FIELDS = [
    "Transaction_ID",
    "Customer_ID",
    "Transaction_DateTime",
    "Transaction_Type",
    "Amount_NGN",
    "Channel",
    "International_Transaction",
    "Transaction_Status",
]

# Device_Type and Location are allowed to be missing — handled in preprocessing.
OPTIONAL_FIELDS = ["Device_Type", "Location"]

ALLOWED_INTERNATIONAL_VALUES = {"Yes", "No"}


def validate_transaction_row(row: dict) -> ValidationResult:
    errors = []

    for f in REQUIRED_FIELDS:
        value = row.get(f)
        if value is None or (isinstance(value, str) and value.strip() == "") or pd.isna(value):
            errors.append(f"Missing required field: {f}")

    if row.get("Amount_NGN") is not None and not pd.isna(row.get("Amount_NGN")):
        try:
            amount = float(row["Amount_NGN"])
            if amount < 0:
                errors.append("Amount_NGN must not be negative")
        except (ValueError, TypeError):
            errors.append(f"Amount_NGN is not a valid number: {row.get('Amount_NGN')!r}")

    if row.get("Transaction_DateTime") is not None and not pd.isna(row.get("Transaction_DateTime")):
        try:
            pd.to_datetime(row["Transaction_DateTime"])
        except Exception:
            errors.append(f"Transaction_DateTime is not a valid datetime: {row.get('Transaction_DateTime')!r}")

    intl = row.get("International_Transaction")
    if intl is not None and not pd.isna(intl) and intl not in ALLOWED_INTERNATIONAL_VALUES:
        errors.append(f"Unexpected category for International_Transaction: {intl!r}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def validate_transaction_batch(df: pd.DataFrame) -> ValidationResult:
    if df is None or df.empty:
        return ValidationResult(is_valid=False, errors=["Input dataset is empty"])

    missing_columns = [c for c in REQUIRED_FIELDS if c not in df.columns]
    if missing_columns:
        return ValidationResult(
            is_valid=False,
            errors=[f"Missing required column: {c}" for c in missing_columns],
        )

    all_errors = []
    for idx, row in df.iterrows():
        result = validate_transaction_row(row.to_dict())
        if not result.is_valid:
            all_errors.append(f"Row {idx} ({row.get('Transaction_ID', 'unknown')}): " + "; ".join(result.errors))

    return ValidationResult(is_valid=len(all_errors) == 0, errors=all_errors)
