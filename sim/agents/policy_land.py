"""A state's choices about land and its debts, put to its decision policy like any other decision.

`debt_relief_tiles` offers a state the tiles where households owe, and returns those its policy picks. Each
option is worth and costs nothing to a value policy (the lenders bear the loss, so no price of the choice is
modelled here), so only a policy that wants relief (a player's, a mod's) chooses it.
"""
from typing import Any, Iterable, List

from .policy import Decision, Option, ValuePolicy

DEBT_RELIEF_DECISION = "debt_relief"


def debt_relief_tiles(actor: Any, indebted_tiles: Iterable[str]) -> List[str]:
	"""The tiles, sorted, whose household debts the actor's state cancels this year."""
	decision = Decision(DEBT_RELIEF_DECISION, [Option(subject=tile, worth=0.0, cost=0.0)
											   for tile in sorted(set(indebted_tiles))], float("inf"))
	policy = getattr(actor, "decision_policy", None) or ValuePolicy()
	return sorted(option.subject for option in policy.choose(actor, decision))
