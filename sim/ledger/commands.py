"""The ledger's commands: every change of a balance is one of these, sent to the ledger."""
from dataclasses import dataclass
from typing import Any

from sim.assembly.api import Command


@dataclass(frozen=True)
class PayEdge(Command):
	"""The acting seat's household pays a named edge (a counterparty the simulation does not model as an actor).
	Never refused for lack of money: a household may go negative, and the credit limit is applied later."""
	edge: str
	amount: float
	purpose: Any                  # a label, or {label: share of the amount}


@dataclass(frozen=True)
class ReceiveFromEdge(Command):
	"""A named edge pays the acting seat's household."""
	edge: str
	amount: float
	purpose: Any


@dataclass(frozen=True)
class PayWages(Command):
	"""The acting seat's household pays wages: the home country's people receive them (the workers edge while there
	are no strata)."""
	amount: float
	purpose: Any


@dataclass(frozen=True)
class ChangeStock(Command):
	"""Tonnes of a commodity (by its commodity key) added to (positive) or taken from (negative) the acting seat's
	stock, counted in this year's opening stock as well, so the year's accounting sees it as held from the start."""
	commodity: str
	tonnes: float
	# Complaint 681, kept until the migration's last equivalence proof: the old living-stock path took the opening
	# snapshot after the change, so the year's first change counts twice in the opening stock
	legacy_snapshot_after_change: bool = False
