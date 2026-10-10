"""Named budget lines for the state's works and for what raising and spending its revenue costs.

Upkeep of the works it holds (walls, water works, monuments; `state_works.py`), the collectors each revenue form
needs, the supply of a force in the field against a threat, and the donative a new ruler pays the army.
"""
import math
from typing import Any, List

from . import budget_lines, state_works
from .budget_line import Line
from .tuning_spending import (CAMPAIGN_SHARE_OF_ARMY_PER_UNIT_THREAT, CUSTOMS_BASE_PER_COLLECTOR_WAGE_YEAR,
							  DONATIVE_SHARE_OF_ANNUAL_PAY, FARM_TAX_BASE_PER_COLLECTOR_WAGE_YEAR, MARCH_KM_PER_DAY,
							  MASONRY_PERSON_YEARS_PER_M2, POLL_TAX_BASE_PER_COLLECTOR_WAGE_YEAR,
							  PROPERTY_TAX_BASE_PER_COLLECTOR_WAGE_YEAR, PUBLIC_BUILDING_LIFE_YEARS, SOLDIER_GRAIN_KG_PER_DAY)

SOLDIER_TRADE = "soldier"
COLLECTOR_TRADE = "scribe"

# How much of a form's base one collector-year handles, by what the form falls on (in wage-years of base);
# a basis not listed is assessed like property.
BASE_PER_COLLECTOR_WAGE_YEAR = {
	"harvest": FARM_TAX_BASE_PER_COLLECTOR_WAGE_YEAR,
	"adult_labour_years": POLL_TAX_BASE_PER_COLLECTOR_WAGE_YEAR,
	"imports_value": CUSTOMS_BASE_PER_COLLECTOR_WAGE_YEAR,
	"exports_value": CUSTOMS_BASE_PER_COLLECTOR_WAGE_YEAR,
}


def works_upkeep_lines(world: Any) -> List[Line]:
	"""One line per work held: the labour that replaces its stock once in a building's life."""
	stock = state_works.held(world)
	lines = []
	for work in state_works.WORKS:
		person_years = stock[work.name] * MASONRY_PERSON_YEARS_PER_M2 / PUBLIC_BUILDING_LIFE_YEARS
		if person_years > 0.0:
			lines.append(budget_lines.paid(world, work.name, "requisition", {work.trade: person_years}))
	return [line for line in lines if line.money > 0.0]


def collection_line(world: Any) -> List[Line]:
	"""Collectors for the forms the state raises: each form's base, counted in years of an unskilled wage, over
	what a collector handles of that kind of base in a year."""
	wage = world.pay_per_person_year("labourer")
	if wage <= 0.0:
		return []
	collectors = 0.0
	for assessed in world.revenue_assessments():
		handled = BASE_PER_COLLECTOR_WAGE_YEAR.get(assessed.basis, PROPERTY_TAX_BASE_PER_COLLECTOR_WAGE_YEAR)
		collectors += assessed.base / wage / handled
	line = budget_lines.paid(world, "tax_collection", "office", {COLLECTOR_TRADE: collectors})
	return [line] if line.money > 0.0 else []


def campaign_line(world: Any, soldiers: float) -> List[Line]:
	"""Grain for the part of the army that takes the field against a threat, over a march out to the frontier and
	back. The army does not move on the map, so the distance is the radius of a region with the frontier's length.
	TEMPORARY HEURISTIC (CLAUDE.md 4.4)."""
	marching = soldiers * min(1.0, CAMPAIGN_SHARE_OF_ARMY_PER_UNIT_THREAT * world.threat_pressure())
	days = 2.0 * (world.territory().frontier_km / (2.0 * math.pi)) / MARCH_KM_PER_DAY
	tonnes = marching * days * SOLDIER_GRAIN_KG_PER_DAY / 1000.0
	if tonnes <= 0.0:
		return []
	return [Line("campaign", "requisition", {}, 0.0, {world.commodity_of(budget_lines.DOLE_MATERIAL): tonnes},
				 world.material_cost(budget_lines.DOLE_MATERIAL, tonnes))]


def donative_line(world: Any, soldiers: float) -> List[Line]:
	"""The gift to each soldier when a new ruler has acceded and it is still unpaid."""
	if not world.government().record.accession_due or soldiers <= 0.0:
		return []
	return [Line("donative", "requisition",
				 transfer=soldiers * world.pay_per_person_year(SOLDIER_TRADE) * DONATIVE_SHARE_OF_ANNUAL_PAY)]
