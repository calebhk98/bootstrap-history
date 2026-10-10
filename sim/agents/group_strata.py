"""Bodies of people (strata) as interest groups: those whose incomes have fallen from what they came to expect."""
from typing import Any, List

from .group_jobs import jobless_sectors, remember_idle
from .group_rent import grievance_parts
from .group_tuning import STRATUM_GRIEVANCE_THRESHOLD, STRATUM_WELFARE_MEMORY_RATE
from .sector import Sector
from .stratum_year import WAGES
from .tuning_strata import STRATUM_WORKING_SHARE

FALLING_INCOMES = "falling_incomes"
DISPLACED_WORKERS = "displaced_workers"
LANDHOLDERS = "landholders"


def organisable(stratum: Any) -> bool:
	"""A free stratum of the home country with people in it; the bonded and foreign cannot act on this state."""
	record = stratum.record
	return record.country is None and record.members > 0.0 and not stratum.is_bonded()


def property_holders(strata: List[Any]) -> List[Any]:
	"""The free strata that hold property, among whom the land market's rent is shared."""
	return [stratum for stratum in strata if organisable(stratum) and float(stratum.record.plan.get("property_share") or 0.0) > 0.0]


def remember_welfare(strata: List[Any], world: Any = None) -> None:
	"""Each year a stratum's expectation moves toward the welfare it has, and with a `world` toward each
	income (wages, property: the land market's rent where land was let) it earns and the share of its trade's
	hours it expects to go unhired."""
	holders = property_holders(strata)
	if world is not None:
		remember_idle([stratum for stratum in strata if organisable(stratum)], world)
	for stratum in strata:
		record = stratum.record
		if not organisable(stratum):
			continue
		if record.welfare_reference <= 0.0:
			record.welfare_reference = record.welfare
		else:
			record.welfare_reference += STRATUM_WELFARE_MEMORY_RATE * (record.welfare - record.welfare_reference)
		if world is None:
			continue
		for component, income in grievance_parts(stratum, holders, world).items():
			reference = record.income_reference.get(component, 0.0)
			record.income_reference[component] = (
				income if reference <= 0.0 else reference + STRATUM_WELFARE_MEMORY_RATE * (income - reference))


def _fallen_incomes(stratum: Any, holders: List[Any], world: Any) -> List[Sector]:
	"""One sector for each income of the stratum (its wages, its property) that has fallen below what it
	expected: workers when their trade's pay fell, landholders when the rent of the land they let fell."""
	record = stratum.record
	sectors = []
	for component, income in sorted(grievance_parts(stratum, holders, world).items()):
		reference = record.income_reference.get(component, 0.0)
		fall = reference - income
		if reference <= 0.0 or fall < STRATUM_GRIEVANCE_THRESHOLD * reference:
			continue
		percent = round(100.0 * fall / reference)
		if component == WAGES:
			trade = record.plan.get("trade")
			working = float(record.plan.get("work_share", STRATUM_WORKING_SHARE))
			sectors.append(Sector(
				DISPLACED_WORKERS, record.stratum, "the %s (%s work)" % (record.name, trade),
				"the pay of %s work has fallen %d%% below what they had come to expect" % (trade, percent),
				fall, reference, record.members * working, 1.0))
		else:
			sectors.append(Sector(
				LANDHOLDERS, record.stratum, "the %s as landholders" % record.name,
				"their rents and property income have fallen %d%% below what they had come to expect" % percent,
				fall, reference, record.members, 1.0))
	return sectors


def stratum_sectors(strata: List[Any], world: Any) -> List[Sector]:
	"""The sectors of the strata whose incomes are below what they expect: workers whose trade's pay fell,
	workers whose jobs went (hours left unhired, with the technique that displaced them) and landholders whose
	rents fell, each by the fall measured; and, for the part of a stratum's fall in welfare those do not
	explain, one sector of falling incomes. The people are its own."""
	sectors = []
	food_cost = world.subsistence_cost_per_person_year()
	holders = property_holders(strata)
	for stratum in strata:
		record = stratum.record
		if not organisable(stratum):
			continue
		named = _fallen_incomes(stratum, holders, world) + jobless_sectors([stratum], world)
		sectors.extend(named)
		if record.welfare_reference <= 0.0:
			continue
		food_bill = record.members * food_cost
		fall = record.welfare_reference - record.welfare
		unexplained = fall * food_bill - sum(sector.lost_income for sector in named)
		if fall < STRATUM_GRIEVANCE_THRESHOLD * record.welfare_reference or unexplained <= 0.0:
			continue
		if unexplained < STRATUM_GRIEVANCE_THRESHOLD * record.welfare_reference * food_bill:
			continue
		owns_property = float(record.plan.get("property_share") or 0.0) > 0.0
		income_word = "rents and property income" if owns_property else "earnings"
		sectors.append(Sector(
			FALLING_INCOMES, record.stratum, "the " + record.name,
			"their %s have fallen %d%% below what they had come to expect" % (
				income_word, round(100.0 * fall / record.welfare_reference)),
			unexplained, record.welfare_reference * food_bill, record.members, 1.0))
	return sectors
