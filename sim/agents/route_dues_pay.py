"""Paying a haul's route dues: which account a holder's dues go into, and splitting a payment among holders."""
from typing import Any, Callable, Container, Mapping, Optional

from . import ledger

DUES_CAUSE = "route dues"


def treasury_of(holder: Any, seats: Container, seat_party: Callable[[Any], Any], registry: Any) -> Any:
	"""The account a country's or seat's dues are paid into: a seat's party, else the country's government."""
	if holder in seats:
		return seat_party(holder)
	return registry.government_of(holder) or registry.ensure_government(str(holder))


def pay_dues(payer: Any, owed: Mapping[Any, float], treasury_for: Callable[[Any], Any], limit: Optional[float] = None) -> float:
	"""The payer pays each holder in `owed` its dues, scaled down so the total never exceeds `limit`; returns the money paid."""
	total = sum(owed.values())
	scale = 1.0 if limit is None or total <= limit else max(0.0, limit) / total
	paid = 0.0
	for holder in sorted(owed):
		amount = owed[holder] * scale
		if amount > 0.0:
			ledger.transfer(payer, treasury_for(holder), amount, DUES_CAUSE)
			paid += amount
	return paid
