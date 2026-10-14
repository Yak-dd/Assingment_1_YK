"""Command-line entry point for the retail analytics pipeline."""

import sys
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from pipeline.reporter import build_summary, format_summary
from pipeline.schema import TransactionRecord
from pipeline.transformer import (
    active_transactions,
    apply_regional_tax,
    calculate_net_margins,
)
from pipeline.validator import validate_records


# Edit this list to try different raw transaction records. Values are strings
# intentionally, just like values read from a CSV file.
def _transaction(
    branch_id: str,
    transaction_date: str,
    customer_tier: str,
    item_count: str,
    revenue: str,
    cost: str,
    region: str,
    is_active: str,
) -> Dict[str, str]:
    """Make one raw transaction row with values still ready for validation."""
    return {
        "branch_id": branch_id,
        "transaction_date": transaction_date,
        "customer_tier": customer_tier,
        "item_count": item_count,
        "revenue": revenue,
        "cost": cost,
        "region": region,
        "is_active": is_active,
    }


TRANSACTIONS = [
    _transaction("BR-01", "2026-09-01", "gold", "3", "120.50", "72.00", "north", "true"),
    _transaction("BR-02", "2026-09-01", "silver", "2", "45.00", "25.00", "south", "true"),
    _transaction("BR-01", "2026-09-02", "gold", "1", "80.00", "44.00", "north", "true"),
    _transaction("BR-03", "2026-09-02", "bronze", "4", "0.00", "0.00", "south", "false"),
    _transaction("BR-02", "2026-09-03", "silver", "2", "67.25", "39.50", "south", "true"),
    _transaction("BR-03", "2026-09-04", "bronze", "2", "52.00", "28.00", "north", "true"),
    _transaction("BR-04", "2026-09-04", "gold", "5", "215.75", "132.00", "west", "true"),
    _transaction("BR-01", "2026-09-05", "silver", "1", "32.50", "18.00", "north", "true"),
    _transaction("BR-02", "2026-09-05", "gold", "3", "148.00", "91.00", "south", "true"),
    _transaction("BR-03", "2026-09-06", "bronze", "2", "27.99", "14.00", "west", "true"),
    _transaction("BR-04", "2026-09-06", "silver", "4", "96.40", "58.00", "north", "true"),
    _transaction("BR-01", "2026-09-07", "gold", "2", "185.00", "112.50", "south", "false"),
    _transaction("BR-02", "2026-09-07", "bronze", "1", "18.75", "9.00", "west", "true"),
    _transaction("BR-03", "2026-09-08", "silver", "3", "74.50", "42.00", "north", "true"),
    _transaction("BR-04", "2026-09-08", "gold", "6", "320.00", "194.00", "south", "true"),
    _transaction("BR-01", "2026-09-09", "bronze", "2", "41.25", "20.00", "west", "true"),
    _transaction("BR-02", "2026-09-09", "silver", "3", "88.00", "52.00", "north", "true"),
    _transaction("BR-03", "2026-09-10", "gold", "2", "137.50", "80.00", "south", "true"),
    _transaction("BR-04", "2026-09-10", "bronze", "1", "-12.00", "5.00", "west", "true"),
    _transaction("BR-01", "not-a-date", "silver", "2", "59.99", "31.00", "north", "true"),
]


def run_pipeline(
    rows: Iterable[Mapping[str, str]],
    regional_tax_rates: Optional[Dict[str, float]] = None,
) -> Tuple[str, Dict[str, object], List[TransactionRecord], List[str]]:
    """Validate transactions, calculate metrics, and format a report."""
    raw_rows = list(rows)
    records, errors = validate_records(raw_rows)
    active = active_transactions(records)
    margins = calculate_net_margins(records)
    tax_adjusted = apply_regional_tax(records, regional_tax_rates or {})
    average_margin = sum(margins) / len(margins) if margins else 0.0
    summary = build_summary(
        len(raw_rows),
        records,
        tax_adjusted,
        len(active),
        average_margin,
    )
    return format_summary(summary), summary, records, errors


def main() -> int:
    """Run the built-in example transactions and print their results."""
    report, _, _, errors = run_pipeline(
        TRANSACTIONS,
        regional_tax_rates={"north": 0.08, "south": 0.06, "west": 0.07},
    )
    print(report)
    if errors:
        print("\nValidation issues:")
        for error in errors:
            print("  - {}".format(error))
    return 0


if __name__ == "__main__":
    sys.exit(main())
