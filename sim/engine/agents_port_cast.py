"""What the cast of countries, players and strata ask of the world, and the roster a game starts with.

A place is a tile or a region id of the geography file; None is where the founder operates from.
A body of people's food costs the staple the dole is paid in, at the market's price, for a person's
subsistence; housing is the yearly carrying cost (interest and wear) of building one person's floor space.
"""
import functools
from typing import Any, Dict, List, Optional, Tuple

from sim.agents.api import (DOLE_MATERIAL, HOUSING_FLOOR_AREA_PER_PERSON_M2, MASONRY_PERSON_YEARS_PER_M2,
							PUBLIC_BUILDING_LIFE_YEARS, cast_from_civilisations, seed_cast)
from sim.geography.api import haversine_km, load_geography, regions

from .data import load_civ


@functools.lru_cache(maxsize=None)
def _place_coordinates(place: str) -> Optional[Tuple[float, float]]:
	land = load_geography()["land_tiles"]
	tile = land["tiles"].get(place)
	if tile is not None:
		return float(tile["lat"]), float(tile["lon"])
	if place in land["region_to_tiles"]:
		return regions.region_anchor(load_geography(), place)
	return None


class CastView:
	"""Mixed into `SimWorld`."""

	def _founder_place(self) -> str:
		return str(self._sim.labour.base_tile())  # type: ignore[attr-defined]

	def distance_km(self, place_a: Optional[str], place_b: Optional[str]) -> float:
		"""Great-circle kilometres between two places; 0 when either is not on the map."""
		first = _place_coordinates(place_a if place_a is not None else self._founder_place())
		second = _place_coordinates(place_b if place_b is not None else self._founder_place())
		if first is None or second is None:
			return 0.0
		return haversine_km(first[0], first[1], second[0], second[1])

	def subsistence_cost_per_person_year(self) -> float:
		tonnes = self.subsistence_kg_per_person_year() / 1000.0  # type: ignore[attr-defined]
		return self.material_cost(DOLE_MATERIAL, tonnes)  # type: ignore[attr-defined,no-any-return]

	def housing_cost_per_person_year(self) -> float:
		"""The labourers' pay to build one person's floor space, carried a year at the market rate and
		worn over a building's life."""
		building = (HOUSING_FLOOR_AREA_PER_PERSON_M2 * MASONRY_PERSON_YEARS_PER_M2
					* self.pay_per_person_year("labourer"))  # type: ignore[attr-defined]
		return building * (self.market_rate() + 1.0 / PUBLIC_BUILDING_LIFE_YEARS)  # type: ignore[attr-defined]

	def observed_stratum(self, country: Optional[str], name: str) -> Optional[Dict[str, float]]:
		"""Nothing is observed yet: the agent economy's cohorts are not mapped to strata (a complaint)."""
		return None


def opening_cast(sim: Any) -> Tuple[str, List[Any], Dict[str, Any]]:
	"""(home country, entries, profiles): the civilisation played, and every economy trading with it."""
	foreign = [load_civ(civilisation_id) for civilisation_id in sim.foreign_economies()]
	return cast_from_civilisations(sim.civ, foreign)


def seed_opening_cast(sim: Any) -> List[str]:
	"""Seed the roster once, at the game's first actor year; the saved roster stands after that."""
	registry = sim.actors
	if registry.state.home_country:
		return []
	home_country, entries, profiles = opening_cast(sim)
	return seed_cast(registry, home_country, entries, profiles)
