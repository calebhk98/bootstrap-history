"""How much of the loan a merchant wants for its carriers' wages it asks for (rule_sets.py).

The wage bill follows the hours its plan wants (`carriage_hours.wage_loans`), and the plan follows the volumes it has
learned. Asked whole, a plan that reads a market as far larger than it is asks for more than every saver holds, takes
all of it and sets the rate for everyone. Under the clearing rules the loan is held to the leverage a merchant's cargo
loans are held to (`merchants_credit.MERCHANT_LEVERAGE_LIMIT`)."""
from typing import Optional

from . import carriage_funding
from .merchants_credit import MERCHANT_LEVERAGE_LIMIT


def as_wanted(wanted: Optional[float], _capital: float, _debt: float) -> Optional[float]:
    """The whole of what the wage bill leaves uncovered; the savings on offer ration it."""
    return wanted


def within_leverage(wanted: Optional[float], capital: float, debt: float) -> Optional[float]:
    """What the merchant's leverage limit leaves of it (`carriage_funding.loan_within_leverage`)."""
    return carriage_funding.loan_within_leverage(wanted, MERCHANT_LEVERAGE_LIMIT, capital, debt)
