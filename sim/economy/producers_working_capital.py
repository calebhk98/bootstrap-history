"""A producer's working-capital request, as a plain function of figures the close has already worked out.

The loan backs next year's running costs for one year; what stands behind it is the producer's own cash, the goods it
holds (stock in hand is what a merchant pledges for credit) and its plant, so the risk markup (credit.risk_premium)
reads those and not the loan itself.
"""
from typing import Iterable, Optional, Tuple

from .types import LoanRequest

WORKING_CAPITAL_PURPOSE = "working capital"     # a loan for next year's running costs, never for plant


def pledgeable_assets(cash: float, goods: Iterable[Tuple[Optional[float], float]], plant_value: float) -> float:
    """Cash, plus each held good as (price, quantity) at the price it has (a good with no price counts for nothing,
    a negative quantity for nothing), plus the plant at replacement cost."""
    held = sum(price * quantity for price, quantity in goods if price is not None and price > 0.0 and quantity > 0.0)
    return max(0.0, cash) + held + max(0.0, plant_value)


def request(borrower: str, currency: str, amount: float, maximum_rate: float, assets: float) -> LoanRequest:
    """A one-year loan of `amount`; the collateral is `assets`, or the loan itself when the producer holds none."""
    return LoanRequest(borrower, currency, amount, maximum_rate, 1.0, assets if assets > 0.0 else amount, WORKING_CAPITAL_PURPOSE)
