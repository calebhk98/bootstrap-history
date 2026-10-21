"""Unrest on a tile, from what the state takes and gives, hunger and the burden of collective liability, and the rising it arms.

    grievance = max(0, taken + owed - given) / income_base                       taken: taxes, levies, confiscation
    pressure  = grievance + hunger + liability_burden
    unrest    = 1 - exp(-pressure)                                               share of the tile's people discontented
    rising    = people * unrest * ARMED_SHARE_OF_DISCONTENTED * organisation      soldiers the discontented can put up

A rising forms on a tile when its discontented, armed, would be at least as likely as not to beat the garrison there
(battle.py), so nothing sets how often a state is rebelled against. Factions are the country's interest groups
(group.py): their members' grievances are the people-weighted mean over the country, and their members are the ones a rising
can be organised from. A take people have grown used to is no grievance (`adapted`). Plain functions of numbers."""
import math
from typing import Dict, Optional, Sequence, Tuple

from sim.constants import declare
from sim.world import battle

from . import liability

ARMED_SHARE_OF_DISCONTENTED = declare(
	"ARMED_SHARE_OF_DISCONTENTED", 0.2, kind="temporary_heuristic",
	unit="share of the discontented", source=None, confidence="D",
	retire="Complaints/486: households as actors with arms, leaders and organisation",
	why="Share of a tile's discontented people who take up arms in a rising (men of fighting age with something "
		"to fight with). No source opened gives it; stands in for a model of who joins and who leads.")
RISING_EQUIPMENT_SHARE_OF_REFERENCE = declare(
	"RISING_EQUIPMENT_SHARE_OF_REFERENCE", 0.25, kind="temporary_heuristic",
	unit="share of the reference soldier's iron and ammunition", source=None, confidence="D",
	retire="Complaints/486: households as actors with arms, leaders and organisation",
	why="What the arms of a rising come to against a soldier's kit: tools, hunting gear and what was taken from "
		"the state's stores. Stands in for the stock of arms the households hold.")
GRIEVANCE_ADAPTATION_PER_YEAR = declare(
	"GRIEVANCE_ADAPTATION_PER_YEAR", 0.2, kind="temporary_heuristic",
	unit="share of the gap closed per year", source=None, confidence="D",
	retire="Complaints/486: households as actors with arms, leaders and organisation",
	why="How fast people grow used to what the state takes, so that only a take above what they have got used to is a "
		"grievance. Stands in for expectation and custom; the opening take is the custom a game starts with.")
ORGANISED_FLOOR = declare(
	"ORGANISED_FLOOR", 0.1, kind="temporary_heuristic",
	unit="share of the discontented", source=None, confidence="D",
	retire="Complaints/486: households as actors with arms, leaders and organisation",
	why="The share of a tile's discontented who can act together with no faction to lead them (kin, a village, a "
		"preacher). Stands in for leaders and organisation as actors.")
CONFISCATION_MEMORY_PER_YEAR = declare(
	"CONFISCATION_MEMORY_PER_YEAR", 0.7, kind="temporary_heuristic",
	unit="share kept per year", source=None, confidence="D",
	retire="Complaints/486: households as actors with arms, leaders and organisation",
	why="How much of a tile's grievance over land taken from its holders is still felt a year later. Stands in "
		"for memory and for the holders' kin.")


def grievance(taken: float, owed: float, given: float, income_base: float) -> float:
	"""What the state took (taxes, levies, confiscation) and owes (unpaid claims) beyond what it gave (relief, pay),
	as a share of the income of those it took from; zero where the base is not positive."""
	if income_base <= 0.0:
		return 0.0
	return max(0.0, taken + owed - given) / income_base


def adapted(current: float, reference: float) -> float:
	"""The part of a take above what people have grown used to."""
	return max(0.0, current - reference)


def adapt(reference: float, current: float) -> float:
	"""The reference after a year: it closes `GRIEVANCE_ADAPTATION_PER_YEAR` of the gap to what was taken."""
	return reference + GRIEVANCE_ADAPTATION_PER_YEAR * (current - reference)


def organisation(faction_members: float, people: float) -> float:
	"""Share of the discontented who act together: the factions' members over the people, no less than the floor."""
	share = 0.0 if people <= 0.0 else min(1.0, max(0.0, faction_members) / people)
	return max(ORGANISED_FLOOR, share)


def hunger(eaten_over_need: Optional[float]) -> Optional[float]:
	"""Share of its need a tile's people went short of; None when the economy booked no food for the tile."""
	if eaten_over_need is None:
		return None
	return max(0.0, min(1.0, 1.0 - eaten_over_need))


def liability_burden(rule: str, rate: float, registered: float, remaining: float, remission: float = 0.0) -> float:
	"""How much heavier a stayer's take is under the state's liability rule than under an individual one (0 when equal;
	a tile with no payers left owes nothing)."""
	own = liability.stayers_share_taken(liability.INDIVIDUAL, rate, registered, remaining, remission)
	held = liability.stayers_share_taken(rule, rate, registered, remaining, remission)
	if own is None or held is None or own <= 0.0:
		return 0.0
	return max(0.0, held / own - 1.0)


def faction_grievance(factions: Sequence[Tuple[float, float]], people: float) -> float:
	"""People-weighted grievance of the factions (members, grievance) over `people`; members are counted once at most."""
	if people <= 0.0:
		return 0.0
	return sum(min(members, people) * max(0.0, grievance_share) for members, grievance_share in factions) / people


def unrest(grievance_share: float, hunger_share: Optional[float], burden: float) -> float:
	"""Share of a tile's people discontented, 0 to 1, rising with every pressure and never reaching one."""
	pressure = max(0.0, grievance_share) + max(0.0, hunger_share or 0.0) + max(0.0, burden)
	return 1.0 - math.exp(-pressure)


def rising_soldiers(people: float, unrest_share: float, organised: float = 1.0) -> float:
	"""The armed men a tile's discontented put up, of those who act together."""
	return (max(0.0, people) * max(0.0, min(1.0, unrest_share)) * ARMED_SHARE_OF_DISCONTENTED
			* max(0.0, min(1.0, organised)))


def rising_strength(soldiers: float, reference_kg: float) -> float:
	"""Effective strength of a rising's soldiers: full supply, the equipment of the households."""
	return battle.effective_strength(soldiers, RISING_EQUIPMENT_SHARE_OF_REFERENCE * reference_kg, reference_kg, 1.0)


def rises(rising: float, garrison: float) -> bool:
	"""Whether a tile's discontented rise: when, armed as they are, they would more likely than not beat the garrison."""
	return rising > 0.0 and battle.attacker_win_probability(rising, garrison) >= 0.5


def fade_memory(by_tile: Dict[str, float]) -> Dict[str, float]:
	"""A year's fading of the land-taken grievance by tile; what falls to nothing is forgotten."""
	return {tile: value * CONFISCATION_MEMORY_PER_YEAR for tile, value in by_tile.items()
			if value * CONFISCATION_MEMORY_PER_YEAR > 1e-6}
