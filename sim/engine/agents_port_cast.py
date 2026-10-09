"""What the cast of countries, players and strata ask of the world, and the roster a game starts with.

A place is a tile or a region id of the geography file; None is where the founder operates from.
A body of people's food costs the staple the dole is paid in, at the market's price, for a person's
subsistence; housing is the yearly carrying cost (interest and wear) of building one person's floor space.
"""
import functools
from typing import Any, Dict, List, Optional, Tuple

from sim.agents.api import DOLE_MATERIAL, FOOD_NEED, cast_from_civilisations, observed_incomes, seed_cast
from sim.geography.api import haversine_km, load_geography, regions
from sim.world import need_basket

from . import market_demand
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

	def need_floor_costs_per_person_year(self) -> Dict[str, float]:
		"""What one person's floor of each need costs a year at the prices households pay: the economy's own
		tile prices on each tile's climate floors (the need-basket kernel, sim/world/need_basket.py). While the
		economy opens, the same kernel on the engine's goods market prices. A need with no priced good is left
		out; with none priced, the food floor is the dole."""
		from_tiles = self._sim.economy.agent_need_floor_costs()  # type: ignore[attr-defined]
		if from_tiles:
			return from_tiles
		basket = market_demand.household_basket(self._sim.civ, self._sim.world_map)
		prices = self._sim.goods_market.household_prices()  # type: ignore[attr-defined]
		costs = {need.spec.need_id: need.price_index * need.spec.subsistence_per_person
				 for need in need_basket.need_prices(basket, prices.get) if need.spec.subsistence_per_person > 0.0}
		if not costs:
			tonnes = self.subsistence_kg_per_person_year() / 1000.0  # type: ignore[attr-defined]
			costs[FOOD_NEED] = self.material_cost(DOLE_MATERIAL, tonnes)  # type: ignore[attr-defined]
		return costs

	def country_economy(self, country: str) -> Any:
		"""The agent economy's answers for a partner country that is part of it; None for any other."""
		return self._once("country:" + country, lambda: self._sim.economy.agent_country(country))  # type: ignore[attr-defined]

	def subsistence_cost_per_person_year(self) -> float:
		"""The food floor of `need_floor_costs_per_person_year`."""
		return self.need_floor_costs_per_person_year().get(FOOD_NEED, 0.0)

	def observed_stratum(self, country: Optional[str], name: str) -> Optional[Dict[str, float]]:
		"""The home strata's income from the agent economy's household cohorts (`sim/agents/strata_observed.py`);
		None for another country, or while the economy opens (the strata then keep their own wage bridge)."""
		if country is not None:
			return None
		curve = self._sim.economy.agent_cohort_incomes()  # type: ignore[attr-defined]
		if not curve:
			return None
		home = [actor for actor in self._sim.actors.of_kind("stratum")  # type: ignore[attr-defined]
				if actor.record.country is None and actor.record.exited_year is None]
		income = observed_incomes(home, self, curve).get(name)
		return None if income is None else {"income": income}


def opening_cast(sim: Any) -> Tuple[str, List[Any], Dict[str, Any]]:
	"""(home country, entries, profiles): the civilisation played, and every economy trading with it."""
	foreign = [load_civ(civilisation_id) for civilisation_id in sim.partner_countries()]
	return cast_from_civilisations(sim.civ, foreign)


def seed_opening_cast(sim: Any) -> List[str]:
	"""Seed the roster once, at the game's first actor year; the saved roster stands after that."""
	registry = sim.actors
	if registry.state.home_country:
		return []
	home_country, entries, profiles = opening_cast(sim)
	return seed_cast(registry, home_country, entries, profiles)
