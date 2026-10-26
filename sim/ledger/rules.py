"""The ledger's rules as plain functions of the accounts they change."""
from typing import Any, Dict

from sim.agents.api import payroll


def add_tonnes(stock: Dict[str, float], opening: Dict[str, float], commodity: str, tonnes: float) -> None:
	"""Tonnes added to (or, negative, taken from) a holder's stock and to this year's opening snapshot of it. The
	snapshot is taken before the change, so a holder's first change of a year is not counted twice."""
	stock[commodity] += tonnes
	opening[commodity] = opening.get(commodity, 0.0) + tonnes


def pay_wages(registry: Any, payer: Any, amount: float, purpose: Any, workers_edge: Any) -> None:
	"""Wages reach the free strata in proportion to their members, or the workers edge while there are none."""
	payroll.pay_households(registry, payer, amount, purpose, workers_edge)
