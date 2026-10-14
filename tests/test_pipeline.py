"""Unit tests for retail transaction validation and analysis."""

import unittest
from datetime import date

from main import run_pipeline
from pipeline.schema import TransactionRecord
from pipeline.transformer import (
    active_transactions,
    apply_regional_tax,
    calculate_net_margins,
)
from pipeline.validator import validate_records


def valid_row(**overrides):
    row = {
        "branch_id": "BR-01",
        "transaction_date": "2026-09-01",
        "customer_tier": "gold",
        "item_count": "2",
        "revenue": "100.00",
        "cost": "60.00",
        "region": "north",
        "is_active": "true",
    }
    row.update(overrides)
    return row


class ValidationTests(unittest.TestCase):
    def test_coerces_valid_row_to_typed_record(self):
        records, errors = validate_records([valid_row()])
        self.assertEqual(errors, [])
        self.assertEqual(records[0].transaction_date, date(2026, 9, 1))
        self.assertEqual(records[0].item_count, 2)
        self.assertEqual(records[0].revenue, 100.0)
        self.assertIsInstance(records[0], TransactionRecord)

    def test_rejects_missing_branch_and_negative_revenue(self):
        records, errors = validate_records(
            [
                valid_row(branch_id=""),
                valid_row(revenue="-1"),
                valid_row(item_count="-1"),
                valid_row(revenue="nan"),
            ]
        )
        self.assertEqual(records, [])
        self.assertEqual(len(errors), 4)
        self.assertIn("branch_id is required", errors[0])
        self.assertIn("revenue cannot be negative", errors[1])
        self.assertIn("item_count cannot be negative", errors[2])
        self.assertIn("revenue must be a finite number", errors[3])


class TransformationTests(unittest.TestCase):
    def test_transformations_preserve_source_and_apply_tax(self):
        records, _ = validate_records(
            [valid_row(), valid_row(branch_id="BR-02", is_active="false")]
        )
        active = active_transactions(records)
        margins = calculate_net_margins(records)
        adjusted = apply_regional_tax(records, {"north": 0.08})

        self.assertEqual(len(active), 1)
        self.assertEqual(margins, [0.4, 0.4])
        self.assertEqual(adjusted[0].tax_amount, 8.0)
        self.assertEqual(adjusted[0].total_with_tax, 108.0)
        self.assertEqual(len(records), 2)


class PipelineTests(unittest.TestCase):
    def test_summary_reports_retention_sales_and_tier_counts(self):
        report, summary, _, errors = run_pipeline(
            [valid_row(), valid_row(revenue="-5")]
        )
        self.assertEqual(len(errors), 1)
        self.assertEqual(summary["retention_rate"], 50.0)
        self.assertEqual(summary["active_transactions"], 1)
        self.assertEqual(summary["average_net_margin"], 0.4)
        self.assertEqual(summary["total_revenue"], 100.0)
        self.assertEqual(summary["top_branch"], "BR-01")
        self.assertEqual(summary["tier_counts"], {"gold": 1})
        self.assertIn("Total revenue: $100.00", report)


if __name__ == "__main__":
    unittest.main()
