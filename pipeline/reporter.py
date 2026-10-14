"""Aggregation and terminal formatting for pipeline results."""

from typing import Dict, List, Optional

from pipeline.schema import TransactionRecord
from pipeline.transformer import TaxAdjustedTransaction


def build_summary(
    total_rows: int,
    records: List[TransactionRecord],
    tax_adjusted: List[TaxAdjustedTransaction],
    active_count: int,
    average_net_margin: float,
) -> Dict[str, object]:
    """Build aggregate metrics from validated records."""
    branch_sales: Dict[str, float] = {}
    tier_counts: Dict[str, int] = {}
    for record in records:
        branch_sales[record.branch_id] = (
            branch_sales.get(record.branch_id, 0.0) + record.revenue
        )
        tier_counts[record.customer_tier] = (
            tier_counts.get(record.customer_tier, 0) + 1
        )

    top_branch: Optional[str] = None
    if branch_sales:
        top_branch = max(branch_sales, key=branch_sales.get)

    retained = len(records) / total_rows * 100 if total_rows else 0.0
    return {
        "total_rows": total_rows,
        "valid_rows": len(records),
        "rejected_rows": total_rows - len(records),
        "retention_rate": retained,
        "active_transactions": active_count,
        "average_net_margin": average_net_margin,
        "total_revenue": sum(record.revenue for record in records),
        "top_branch": top_branch,
        "branch_sales": branch_sales,
        "tier_counts": tier_counts,
        "estimated_tax": sum(item.tax_amount for item in tax_adjusted),
    }


def format_summary(summary: Dict[str, object]) -> str:
    """Format the aggregated metrics as a readable terminal report."""
    top_branch = summary["top_branch"] or "N/A"
    tiers = summary["tier_counts"]
    lines = [
        "Retail Analytics Pipeline",
        "=" * 26,
        "Records processed: {}/{}".format(
            summary["valid_rows"], summary["total_rows"]
        ),
        "Rejected records: {}".format(summary["rejected_rows"]),
        "Clean record retention: {:.1f}%".format(summary["retention_rate"]),
        "Active transactions: {}".format(summary["active_transactions"]),
        "Average net margin: {:.1f}%".format(
            summary["average_net_margin"] * 100
        ),
        "Total revenue: ${:,.2f}".format(summary["total_revenue"]),
        "Estimated tax: ${:,.2f}".format(summary["estimated_tax"]),
        "Top-performing branch: {}".format(top_branch),
        "Customer tiers:",
    ]
    if tiers:
        lines.extend(
            "  - {}: {}".format(tier, count)
            for tier, count in sorted(tiers.items())
        )
    else:
        lines.append("  - No valid transactions")
    return "\n".join(lines)
