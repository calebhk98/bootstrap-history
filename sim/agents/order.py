"""The staff that keep order and keep the mines' claims: how many a state keeps, and the two budget lines that pay them.

Guards watch the people of a tile against thieves; foresters keep the woodland tenure of a tile; inspectors check the claims and workings of a tile against the
registry. Each is people hired in a trade at the going wage, so the state competes for them in the labour market like
any employer. How far they reach is read the way collection is (`collection.tile_shares`): their working year, the days
a person's tile asks of them, the road from the seat.

    guards_kept = people * watch_days_per_person / working_days_per_year
"""
from typing import Any, List

from .budget_line import Line
from .revenue_labour import HOURS_PER_WORKING_DAY
from .tuning_order import FORESTER_DAYS_PER_PERSON, INSPECTION_DAYS_PER_PERSON, PATROL_DAYS_PER_PERSON

GUARDS_LINE = "guards"
INSPECTORS_LINE = "inspectors"
FORESTERS_LINE = "foresters"
STAFF_LINES = (GUARDS_LINE, INSPECTORS_LINE, FORESTERS_LINE)   # the standing lines of the state's order staff
GUARD_TRADE = "labourer"
INSPECTOR_TRADE = "scribe"
FORESTER_TRADE = "labourer"


def staff_kept(people: float, days_per_person: float, working_days: float) -> float:
	"""Staff whose working years just cover `days_per_person` of every person, before any road."""
	if people <= 0.0 or working_days <= 0.0:
		return 0.0
	return people * days_per_person / working_days


def guards_kept(people: float, working_days: float) -> float:
	return staff_kept(people, PATROL_DAYS_PER_PERSON, working_days)


def inspectors_kept(people: float, working_days: float) -> float:
	return staff_kept(people, INSPECTION_DAYS_PER_PERSON, working_days)


def foresters_kept(people: float, working_days: float) -> float:
	return staff_kept(people, FORESTER_DAYS_PER_PERSON, working_days)


def working_days_of(world: Any) -> float:
	return float(world.hours_per_person_year) / HOURS_PER_WORKING_DAY


def staff_line(world: Any, name: str, trade: str, kept: float) -> List[Line]:
	if kept <= 0.0:
		return []
	return [Line(name, "office", {trade: kept}, kept * world.pay_per_person_year(trade))]


def guards_line(world: Any) -> List[Line]:
	return staff_line(world, GUARDS_LINE, GUARD_TRADE, guards_kept(world.population_total(), working_days_of(world)))


def inspectors_line(world: Any) -> List[Line]:
	return staff_line(world, INSPECTORS_LINE, INSPECTOR_TRADE,
					  inspectors_kept(world.population_total(), working_days_of(world)))


def foresters_line(world: Any) -> List[Line]:
	return staff_line(world, FORESTERS_LINE, FORESTER_TRADE,
					  foresters_kept(world.population_total(), working_days_of(world)))
