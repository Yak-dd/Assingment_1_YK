"""Data models used by the retail analytics pipeline."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class TransactionRecord:
    """A transaction after its required fields have been validated."""

    branch_id: str
    transaction_date: date
    customer_tier: str
    item_count: int
    revenue: float
    cost: float
    region: str
    is_active: bool

    @property
    def net_margin(self) -> float:
        """Return margin as a fraction of gross revenue, or zero without revenue."""
        if self.revenue == 0:
            return 0.0
        return (self.revenue - self.cost) / self.revenue
