"""Where property income goes: for now each payment reaches the payee unchanged."""
from typing import Sequence

from .types import Transfer


def spread(record, payments: Sequence[Transfer]) -> Sequence[Transfer]:
    return payments
