"""The works a state raises and keeps: each a named stock, with the driver that says how much of it the state wants.

Stock is counted as square metres of masonry (a wall or a conduit is counted as the floor area of building that
takes the same mason's labour), so one rate of labour per unit prices all of them. Upkeep is a standing line
(`budget_works.py`); a surplus buys the gap between the stock held and the stock wanted, in the order below.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple

from .tuning_spending import (CAPITAL_MASONRY_M2_PER_URBAN_PERSON_PER_SPECTACLE_WEIGHT, FORTIFIED_SHARE_OF_FRONTIER_PER_UNIT_THREAT,
							  WALL_MASONRY_EQUIVALENT_M2_PER_M, WATER_MASONRY_EQUIVALENT_M2_PER_URBAN_PERSON)

MASON = "mason"
SPECTACLE_WEIGHT = "spectacle"   # the state's taste for monuments, among the weights it values gains by


@dataclass(frozen=True)
class Work:
	name: str
	trade: str
	wanted: Callable[[Any], float]   # stock the state wants, from the world
	opening_share: float             # share of the stock wanted that stands when the game opens


def fortifications_wanted(world: Any) -> float:
	"""Walls along the share of the land frontier a sack threatens; none without a threat."""
	walled = min(1.0, FORTIFIED_SHARE_OF_FRONTIER_PER_UNIT_THREAT * world.threat_pressure())
	return world.territory().frontier_km * 1000.0 * walled * WALL_MASONRY_EQUIVALENT_M2_PER_M


def water_works_wanted(world: Any) -> float:
	return world.urban_population() * WATER_MASONRY_EQUIVALENT_M2_PER_URBAN_PERSON


def capital_buildings_wanted(world: Any) -> float:
	"""Temples and monuments of the capital, wanted as far as the state values spectacle."""
	return (world.urban_population() * CAPITAL_MASONRY_M2_PER_URBAN_PERSON_PER_SPECTACLE_WEIGHT
			* max(0.0, world.state_weights().get(SPECTACLE_WEIGHT, 0.0)))


# TEMPORARY HEURISTIC (CLAUDE.md 4.4): walls and water works stand at the opening in the measure the drivers want;
# monuments are raised from a surplus only.
WORKS = (
	Work("fortifications", MASON, fortifications_wanted, 1.0),
	Work("water_works", MASON, water_works_wanted, 1.0),
	Work("capital_buildings", MASON, capital_buildings_wanted, 0.0),
)


def held(world: Any) -> Dict[str, float]:
	"""The state's stock of each work, set at the opening to the share of what is wanted that stands then."""
	stock = world.government().record.works_stock
	for work in WORKS:
		if work.name not in stock:
			stock[work.name] = work.opening_share * work.wanted(world)
	return stock


def wear(stock: Dict[str, float], funded: float, life_years: float) -> None:
	"""Works whose upkeep went unpaid decay over their life."""
	for name in stock:
		stock[name] = max(0.0, stock[name] * (1.0 - (1.0 - funded) / life_years))


def gaps(world: Any) -> List[Tuple[Work, float]]:
	"""(work, units short of what is wanted) for each work below its wanted stock, in order."""
	stock = held(world)
	return [(work, work.wanted(world) - stock[work.name]) for work in WORKS if work.wanted(world) > stock[work.name]]
