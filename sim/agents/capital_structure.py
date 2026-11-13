"""A firm raises growth money as debt or as equity, whichever costs it less.

Debt costs the rate the lenders ask of it. Equity costs what the shares give up each year per unit raised: the
dividends the new holders are paid over the price they pay, which is the yield their valuation implies. Where
no investor will take the shares, equity is not open and the firm borrows."""
from typing import Optional

EQUITY_REFUSED_KEY = "equity_refused_year"


def cost_of_equity(dividend_a_year: float, whole_equity_worth: float) -> Optional[float]:
	"""The yield on the shares the firm would sell: the dividend it pays a year over what all its equity is worth.
	None when the equity is worth nothing."""
	if whole_equity_worth <= 0.0:
		return None
	return dividend_a_year / whole_equity_worth


def prefers_equity(debt_rate: float, equity_cost: Optional[float], equity_open: bool) -> bool:
	"""Equity when it is open and costs strictly less than the debt; otherwise debt."""
	return equity_open and equity_cost is not None and equity_cost < debt_rate
