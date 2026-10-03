"""What a state maintains beyond its army and officials, each from a stock it holds.

Roads from the length of road between the tiles it holds, public buildings from the
town dwellers they serve, a court from the officials, a dole from the town poor, and
a navy from the coast to be kept. Each is people at the going wage or goods at the
market's price, so it is demand like any other.
"""
from typing import Any, Dict, List

from .budget_line import Line
from .tuning_spending import (CARPENTERS_PER_SHIP, COAST_KM_PER_SHIP, COURT_RETAINERS_PER_OFFICIAL,
							  CREW_PER_SHIP, DOLE_SHARE_OF_URBAN_PEOPLE, MASONRY_PERSON_YEARS_PER_M2,
							  PUBLIC_BUILDING_LIFE_YEARS, PUBLIC_FLOOR_AREA_PER_URBAN_PERSON_M2,
							  MAX_STATE_SHARE_OF_TRADE, ROAD_UPKEEP_PERSON_YEARS_PER_KM)

# The staple the dole is paid in, as a material in the tree's own terms.
DOLE_MATERIAL = "wheat_kg"


def paid(world: Any, name: str, kind: str, people: Dict[str, float]) -> Line:
	"""A line made only of people kept in trades, never more of a trade than the state can take."""
	people = {trade: min(count, MAX_STATE_SHARE_OF_TRADE * world.national_people(trade)) if trade != "labourer" else count
			  for trade, count in people.items()}
	people = {trade: count for trade, count in people.items() if count > 0.0}
	return Line(name, kind, people, sum(count * world.pay_per_person_year(trade) for trade, count in people.items()))


def roads_line(world: Any) -> List[Line]:
	person_years = world.territory().road_km * ROAD_UPKEEP_PERSON_YEARS_PER_KM
	return [paid(world, "roads", "requisition", {"labourer": person_years})] if person_years > 0.0 else []


def public_buildings_line(world: Any) -> List[Line]:
	stock_m2 = world.urban_population() * PUBLIC_FLOOR_AREA_PER_URBAN_PERSON_M2
	masons = stock_m2 * MASONRY_PERSON_YEARS_PER_M2 / PUBLIC_BUILDING_LIFE_YEARS
	return [paid(world, "public_buildings", "requisition", {"mason": masons})] if masons > 0.0 else []


def court_line(world: Any, officials: float) -> List[Line]:
	if officials <= 0.0:
		return []
	return [paid(world, "court", "office", {"labourer": officials * COURT_RETAINERS_PER_OFFICIAL})]


def dole_line(world: Any) -> List[Line]:
	recipients = world.urban_population() * DOLE_SHARE_OF_URBAN_PEOPLE
	tonnes = recipients * world.subsistence_kg_per_person_year() / 1000.0
	if tonnes <= 0.0:
		return []
	return [Line("dole", "requisition", {}, 0.0, {world.commodity_of(DOLE_MATERIAL): tonnes},
				 world.material_cost(DOLE_MATERIAL, tonnes))]


def navy_line(world: Any) -> List[Line]:
	ships = world.territory().coast_km / COAST_KM_PER_SHIP
	if ships <= 0.0 or not world.trade_exists("sailor"):
		return []
	return [paid(world, "navy", "requisition",
				 {"sailor": ships * CREW_PER_SHIP, "carpenter": ships * CARPENTERS_PER_SHIP})]
