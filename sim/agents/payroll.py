"""Money that lands with households: the people's strata take wages, interest and the state's pay.

A body of people is a stratum actor with a purse. Wages, the state's pay and the interest lenders earn
are shared among the home country's free strata, so the money reaches the people who earn it and what
they pay back (taxes, spending) is paid from their own purses. Where no stratum exists yet, the money
goes to a named edge instead.
"""
from typing import Any, List

from . import ledger
from .edges import EDGE_WORKERS


def free_strata(registry: Any) -> List[Any]:
	"""The home country's strata of free people: bonded people are paid through their keeper."""
	return [stratum for stratum in registry.of_kind("stratum")
			if stratum.record.country is None and stratum.record.exited_year is None
			and not stratum.is_bonded() and stratum.record.members > 0.0]


def pay_households(registry: Any, payer: Any, amount: float, purpose: Any, fallback: Any) -> None:
	"""`payer` pays `amount` to the free strata in proportion to their members, or to `fallback`
	(an edge) when there are none."""
	people = free_strata(registry)
	if not people:
		ledger.transfer(payer, fallback, amount, purpose)
		return
	share_out(payer, people, [stratum.record.members for stratum in people], amount, purpose)


def share_out(payer: Any, payees: List[Any], weights: List[float], amount: float, purpose: Any) -> None:
	"""Move `amount` from `payer` to each payee by weight; the last takes the remainder so none is lost."""
	total = sum(weights)
	if amount == 0.0 or total <= 0.0:
		return
	moved = 0.0
	for index, payee in enumerate(payees):
		part = amount - moved if index == len(payees) - 1 else amount * weights[index] / total
		ledger.transfer(payer, payee, part, purpose)
		moved += part


def pay_savers(registry: Any, payer: Any, amount: float) -> None:
	"""Interest the people earn as lenders: to the free strata in proportion to what they hold saved."""
	savers = [stratum for stratum in free_strata(registry) if stratum.money > 0.0]
	if savers:
		share_out(payer, savers, [stratum.money for stratum in savers], amount, "interest_on_lending")


def pay_wages(registry: Any, payer: Any, amount: float, purpose: Any, world: Any) -> None:
	"""Wages: to the people, or to the workers edge while there are no strata."""
	pay_households(registry, payer, amount, purpose, world.edge(EDGE_WORKERS))
