"""Stateless transformations for validated retail transactions."""

from dataclasses import dataclass
from typing import Dict, Iterable, List

from pipeline.schema import TransactionRecord


@dataclass(frozen=True)
class TaxAdjustedTransaction:
    """A transaction with its regional tax estimate applied separately."""

    transaction: TransactionRecord
    tax_rate: float
    tax_amount: float

    @property
    def total_with_tax(self) -> float:
        """Return gross revenue plus the calculated tax."""
        return self.transaction.revenue + self.tax_amount


def active_transactions(
    records: Iterable[TransactionRecord],
) -> List[TransactionRecord]:
    """Return active records without changing the input collection."""
    return list(filter(lambda record: record.is_active, records))


def calculate_net_margins(
    records: Iterable[TransactionRecord],
) -> List[float]:
    """Return each transaction's margin fraction using a functional map."""
    return list(map(lambda record: record.net_margin, records))


def apply_regional_tax(
    records: Iterable[TransactionRecord], tax_rates: Dict[str, float]
) -> List[TaxAdjustedTransaction]:
    """Estimate tax using region rates; regions without a rate use zero."""
    return [
        TaxAdjustedTransaction(
            transaction=record,
            tax_rate=tax_rates.get(record.region, 0.0),
            tax_amount=record.revenue * tax_rates.get(record.region, 0.0),
        )
        for record in records
    ]
