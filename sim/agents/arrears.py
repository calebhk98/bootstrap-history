"""Pay a state owes its army and officials and has not paid: kept as a debt, settled first from later revenue."""
from typing import Any, Dict, List

from .budget_line import Line

# the lines whose people are owed their pay when the year's purse does not cover it
PAY_LINES = ("army", "administration", "court")


def total(record: Any) -> float:
	"""Everything the state owes in unpaid pay."""
	return sum(record.arrears.values())


def owe(record: Any, lines: List[Line], share: float, owed_fraction: float = 1.0) -> None:
	"""Book the part of each pay line the year's purse did not cover as owed, as far as the state chose to defer it
	(`owed_fraction` of what is unpaid; the rest is cut and never owed)."""
	for line in lines:
		unpaid = line.money * (1.0 - share) * owed_fraction
		if line.name in PAY_LINES and unpaid > 0.0:
			record.arrears[line.name] = record.arrears.get(line.name, 0.0) + unpaid


def settle(government: Any, world: Any) -> Dict[str, float]:
	"""Pay what is owed, as far as the purse reaches (never by borrowing), before anything else is paid from it;
	what was paid by line."""
	record = government.record
	record.arrears_paid = {}
	owed = total(record)
	if owed <= 0.0 or government.money <= 0.0:
		return {}
	covered = min(1.0, government.money / owed)
	paid: Dict[str, float] = {}
	for name, amount in sorted(record.arrears.items()):
		if amount > 0.0:
			paid[name] = amount * covered
			world.pay_wages(government, paid[name], name)
			record.arrears[name] = amount - paid[name]
	record.arrears = {name: amount for name, amount in record.arrears.items() if amount > 1e-9}
	record.arrears_paid = paid
	return paid
