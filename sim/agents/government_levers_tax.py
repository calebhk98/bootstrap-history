"""The levers a state pulls on how its taxpayers answer: who is liable for those who left, and the ways back.

Each is a field of the government's `levers` record, read by the same code whoever holds the seat (a player, an AI state):
`liability` (a rule of `liability.RULES`), `amnesty` (the share of a fugitive's arrears waived, so he can return),
`immunity` (years a taker of deserted land owes nothing) and `remission` (the share of every form's tax remitted).
"""
from typing import Any, Dict, Union

from sim.refusal import Refusal

from .liability import INDIVIDUAL, RULES

LIABILITY, AMNESTY, IMMUNITY, REMISSION = "liability", "amnesty", "immunity", "remission"
TAX_KINDS = (LIABILITY, AMNESTY, IMMUNITY, REMISSION)
LIMITS = {AMNESTY: (0.0, 1.0, "a share of arrears waived"), IMMUNITY: (0.0, 50.0, "years of immunity"),
		  REMISSION: (0.0, 1.0, "a share of the tax remitted")}


def set_tax_lever(levers: Dict[str, Any], kind: str, value: Any, number, refuse) -> Union[Dict[str, Any], Refusal]:
	"""Set (None clears) a tax-response lever of `levers`. `number` checks a figure within limits and `refuse` builds a
	refusal (both from government_levers, so a bad request is refused the same way for every lever)."""
	before = levers.get(kind)
	if value is None:
		levers.pop(kind, None)
		return {"lever": kind, "name": None, "before": before, "after": None}
	if kind == LIABILITY:
		if value not in RULES:
			return refuse("unknown_rule", "liability is one of %s." % ", ".join(RULES), list(RULES), value=str(value))
		levers[kind] = value
		return {"lever": kind, "name": None, "before": before, "after": value}
	low, high, what = LIMITS[kind]
	figure = number(value, low, high, what)
	if isinstance(figure, Refusal):
		return figure
	levers[kind] = figure
	return {"lever": kind, "name": None, "before": before, "after": figure}


def liability_rule(record: Any) -> str:
	return record.levers.get(LIABILITY, INDIVIDUAL)


def amnesty_share(record: Any) -> float:
	return float(record.levers.get(AMNESTY, 0.0))


def immunity_years(record: Any) -> float:
	return float(record.levers.get(IMMUNITY, 0.0))


def remission_share(record: Any) -> float:
	return float(record.levers.get(REMISSION, 0.0))
