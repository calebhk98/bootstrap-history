"""Who answers for the tax of those who left: the state's choice of liability rule, for any state.

Under an individual rule each payer owes his own and what the leavers owed is lost to the state. Under a collective rule
the unit (a village, a tile) owes what it was assessed when its payers were all there, so the share each stayer owes
rises as others go. The unit's assessment is the form's rate on every registered payer's income; the stayers split it.

    share_taken_of_stayer = rate * (1 - remission) * registered_payers / remaining_payers      (collective, at most 1)
    share_taken_of_stayer = rate * (1 - remission)                                              (individual)
"""
from typing import Dict, Optional

INDIVIDUAL = "individual"
COLLECTIVE = "collective"
RULES = (INDIVIDUAL, COLLECTIVE)


def stayers_share_taken(rule: str, rate: float, registered: float, remaining: float, remission: float = 0.0) -> Optional[float]:
	"""Share of his income the state takes from a payer who stays, or None when nobody remains to pay."""
	if remaining <= 0.0:
		return None
	own = max(0.0, rate) * (1.0 - max(0.0, min(1.0, remission)))
	if rule == COLLECTIVE:
		return min(1.0, own * max(registered, remaining) / remaining)
	return min(1.0, own)


def shares_by_unit(rule: str, rate: float, registered: Dict[str, float], remaining: Dict[str, float],
				   remission: float = 0.0) -> Dict[str, float]:
	"""`stayers_share_taken` for each unit that still has payers (an emptied unit's debt is cancelled, as a prefect did
	where nobody remained)."""
	shares: Dict[str, float] = {}
	for unit in sorted(registered):
		share = stayers_share_taken(rule, rate, registered[unit], remaining.get(unit, 0.0), remission)
		if share is not None:
			shares[unit] = share
	return shares
