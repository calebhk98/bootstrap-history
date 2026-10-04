"""Bodies of people (strata) as interest groups: those whose incomes have fallen from what they came to expect."""
from typing import Any, List

from .group_tuning import STRATUM_GRIEVANCE_THRESHOLD, STRATUM_WELFARE_MEMORY_RATE
from .sector import Sector

FALLING_INCOMES = "falling_incomes"


def organisable(stratum: Any) -> bool:
	"""A free stratum of the home country with people in it; the bonded and foreign cannot act on this state."""
	record = stratum.record
	return record.country is None and record.members > 0.0 and not stratum.is_bonded()


def remember_welfare(strata: List[Any]) -> None:
	"""Each year a stratum's expectation moves toward the welfare it has."""
	for stratum in strata:
		record = stratum.record
		if not organisable(stratum):
			continue
		if record.welfare_reference <= 0.0:
			record.welfare_reference = record.welfare
		else:
			record.welfare_reference += STRATUM_WELFARE_MEMORY_RATE * (record.welfare - record.welfare_reference)


def stratum_sectors(strata: List[Any], world: Any) -> List[Sector]:
	"""One sector per organisable stratum whose welfare is below what it expects: the loss is the
	shortfall of income against its expectation, the people are its own."""
	sectors = []
	food_cost = world.subsistence_cost_per_person_year()
	for stratum in strata:
		record = stratum.record
		if not organisable(stratum) or record.welfare_reference <= 0.0:
			continue
		fall = record.welfare_reference - record.welfare
		if fall < STRATUM_GRIEVANCE_THRESHOLD * record.welfare_reference:
			continue
		food_bill = record.members * food_cost
		owns_property = float(record.plan.get("property_share") or 0.0) > 0.0
		income_word = "rents and property income" if owns_property else "earnings"
		sectors.append(Sector(
			FALLING_INCOMES, record.stratum, "the " + record.name,
			"their %s have fallen %d%% below what they had come to expect" % (
				income_word, round(100.0 * fall / record.welfare_reference)),
			fall * food_bill, record.welfare_reference * food_bill, record.members, 1.0))
	return sectors
