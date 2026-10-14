"""Validation and type coercion for raw transaction rows."""

from datetime import date
from math import isfinite
from typing import Dict, Iterable, List, Mapping, Tuple

from pipeline.schema import TransactionRecord


def _required_text(row: Mapping[str, str], field: str) -> str:
    value = row.get(field)
    if value is None or not value.strip():
        raise ValueError("{} is required".format(field))
    return value.strip()


def _non_negative_number(row: Mapping[str, str], field: str) -> float:
    value = row.get(field)
    if value is None or not value.strip():
        raise ValueError("{} is required".format(field))
    try:
        number = float(value)
    except ValueError as error:
        raise ValueError("{} must be numeric".format(field)) from error
    if not isfinite(number):
        raise ValueError("{} must be a finite number".format(field))
    if number < 0:
        raise ValueError("{} cannot be negative".format(field))
    return number


def _is_active(row: Mapping[str, str]) -> bool:
    value = row.get("is_active", "true")
    if value is None or not value.strip():
        return True
    normalized = value.strip().lower()
    if normalized in ("true", "yes", "1"):
        return True
    if normalized in ("false", "no", "0"):
        return False
    raise ValueError("is_active must be true/false, yes/no, or 1/0")


def validate_records(
    rows: Iterable[Mapping[str, str]],
) -> Tuple[List[TransactionRecord], List[str]]:
    """Convert valid input rows and report rejected rows with their row numbers."""
    records = []
    errors = []

    for row_number, row in enumerate(rows, start=2):
        try:
            extra_fields = row.get(None)
            if extra_fields:
                raise ValueError("row contains more fields than the CSV header")
            date_text = _required_text(row, "transaction_date")
            item_count = int(_required_text(row, "item_count"))
            if item_count < 0:
                raise ValueError("item_count cannot be negative")
            cost_text = row.get("cost") or ""
            records.append(
                TransactionRecord(
                    branch_id=_required_text(row, "branch_id"),
                    transaction_date=date.fromisoformat(date_text),
                    customer_tier=_required_text(row, "customer_tier"),
                    item_count=item_count,
                    revenue=_non_negative_number(row, "revenue"),
                    cost=(
                        _non_negative_number({"cost": cost_text}, "cost")
                        if cost_text.strip()
                        else 0.0
                    ),
                    region=(row.get("region") or "").strip() or "default",
                    is_active=_is_active(row),
                )
            )
        except (AttributeError, TypeError, ValueError) as error:
            errors.append("row {}: {}".format(row_number, error))

    return records, errors
