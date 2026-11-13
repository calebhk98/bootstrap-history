"""The standing army as a faction of the state: its pay owed, what campaigns plunder, the loyalty that follows, and what it does
when it has none left.

    fall_in_pay_after_plunder = fall_in_pay * (arrears - plunder) / arrears        plunder is set against what the state owes
    defecting_share           = (MUTINY_LOYALTY - loyalty) / MUTINY_LOYALTY         0 at or above the mutiny line, 1 at no loyalty
    army_backing              = defecting_share * total_backing_of_other_factions * ARMY_WEIGHT_SHARE_OF_FACTIONS

A defecting army backs a claimant to the throne beside the interest groups, and the soldiers who defect rise at the seat against
the garrison, which is weaker by those soldiers (the rising rule is `revolt.py`, settled by the stability phase). Plain functions of
numbers; the loyalty itself moves in `group_servants.py`."""
from typing import Dict, Mapping

from sim.constants import declare

from .group_tuning_stakes import MUTINY_LOYALTY

ARMY_FACTION = "soldiers"

ARMY_WEIGHT_SHARE_OF_FACTIONS = declare(
	"ARMY_WEIGHT_SHARE_OF_FACTIONS", 1.0, kind="temporary_heuristic",
	unit="share of the other factions' total backing, at full defection", source=None, confidence="D",
	retire="Complaints/486: morale and commanders as actors",
	why="How much a wholly defected army weighs in a contest for the throne against all the interest groups together. "
		"Stands in for its officers, its position at the seat and its arms.")
CAPTIVE_VALUE_IN_YEARS_OF_UNSKILLED_PAY = declare(
	"CAPTIVE_VALUE_IN_YEARS_OF_UNSKILLED_PAY", 5.0, kind="temporary_heuristic",
	unit="years of an unskilled worker's pay per captive", source=None, confidence="D",
	retire="Complaints/648: captives sold in a market that prices them",
	why="What a captive taken in a campaign is worth to the soldiers who took him, until captives are sold at a price the "
		"market sets.")


def fall_after_plunder(fall: float, arrears: float, plunder: float) -> float:
	"""The fall in the army's pay that is still unmet once plunder is set against what it is owed; unchanged where nothing is owed."""
	if arrears <= 0.0:
		return fall
	return fall * max(0.0, arrears - max(0.0, plunder)) / arrears


def plunder_of_captives(captives: float, unskilled_pay_per_year: float) -> float:
	"""Money's worth the soldiers take with `captives` of the beaten."""
	return max(0.0, captives) * max(0.0, unskilled_pay_per_year) * CAPTIVE_VALUE_IN_YEARS_OF_UNSKILLED_PAY


def defecting_share(loyalty: float) -> float:
	"""The share of the army that has turned from its paymaster: how far its loyalty is below the mutiny line."""
	if loyalty >= MUTINY_LOYALTY:
		return 0.0
	return min(1.0, (MUTINY_LOYALTY - max(0.0, loyalty)) / MUTINY_LOYALTY)


def with_army(backing: Mapping[str, float], defecting: float) -> Dict[str, float]:
	"""The factions' backing with the army counted among them in proportion to the share of it that has defected."""
	result = dict(backing)
	if defecting > 0.0:
		weight = defecting * sum(value for value in backing.values() if value > 0.0) * ARMY_WEIGHT_SHARE_OF_FACTIONS
		if weight > 0.0:
			result[ARMY_FACTION] = weight
	return result


def remaining_garrison(garrison_strength: float, defecting: float) -> float:
	"""The garrison's strength once the defecting share of the army has left it."""
	return max(0.0, garrison_strength) * (1.0 - max(0.0, min(1.0, defecting)))


def rising_soldiers(soldiers: float, defecting: float) -> float:
	"""The soldiers who rise: the defecting share of the army."""
	return max(0.0, soldiers) * max(0.0, min(1.0, defecting))
