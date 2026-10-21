"""What a state asks the simulated world when it assesses revenue: its declared forms and the bases they read."""
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from sim.agents.collection_world import CollectionView
from sim.agents import collection
from sim.agents.api import government_levers, observed_incomes, revenue
from sim.geography.api import arable_hectares, settlement, tiles_held, usable_modes


class RevenueView(CollectionView):
	"""Read-only questions behind a state's revenue; mixed into `SimWorld`."""

	_sim: Any

	def revenue_forms(self) -> List[Dict[str, Any]]:
		"""The forms of revenue the civilisation's state raises, as its data declares them."""
		return government_levers.revenue_forms(self.government().record)  # type: ignore[attr-defined]

	def fugitive_share(self) -> float:
		"""Share of the country's people who are away, having fled the state's take (the economy's fugitives, by tile)."""
		agent = self._sim.economy.agent
		away = {} if agent is None else agent.fugitive_share_by_tile()
		people = self.collection_people_by_tile()  # type: ignore[attr-defined]
		total = sum(people.values())
		return sum(count * away.get(tile, 0.0) for tile, count in people.items()) / total if total > 0.0 else 0.0

	def revenue_assessments(self) -> List[revenue.Assessment]:
		return self._once("assessments", lambda: revenue.assess(self))  # type: ignore[attr-defined,no-any-return]

	def state_revenue(self) -> float:
		"""Money's worth of what the declared forms yield this year, coin and goods taken in kind alike."""
		return sum(assessment.money for assessment in self.revenue_assessments())

	def harvest_tonnes(self) -> float:
		"""Grain the farm harvested last, in tonnes. Before the first harvest, TEMPORARY HEURISTIC (CLAUDE.md
		4.4): the people are taken to have harvested what they eat."""
		sim = self._sim
		kilograms = sim.state.holdings.farm_last_harvest_kg
		if not kilograms > 0.0:
			technique = sim._farm_technique_this_year
			kilograms = (sim._adult_equivalent_population(sim.population)
						 * sim._agriculture.annual_food_demand_kg_per_person(technique.crop))
		return kilograms / 1000.0

	def output_tonnes(self, material: str, tiles: Optional[FrozenSet[str]] = None) -> float:
		"""Tonnes of a material the producers on the state's tiles (only `tiles` when given) made last year."""
		held = set(self.held_tiles()) if tiles is None else set(tiles)
		by_tile = self._sim.economy.agent_output_tonnes_by_tile()
		return sum(row.get(material, 0.0) for tile, row in by_tile.items() if tile in held)

	def material_price(self, material: str) -> float:
		"""Money for one tonne of a material at the price the market quotes."""
		return self.material_cost(material, 1.0) or 0.0  # type: ignore[attr-defined]

	def trade_value(self, direction: str) -> float:
		"""Money's worth of goods imported ("in") or exported ("out") in the last completed year."""
		trade = self._sim.state.economy.foreign_trade_by_year.get(str(self.year - 1), {})  # type: ignore[attr-defined]
		return float(trade.get(direction, 0.0))

	def coin_stock_value(self) -> float:
		"""Money's worth of the coin this society holds, from its coin standard."""
		return self._sim.economy.coin_stock_value()

	def held_tiles(self) -> List[str]:
		return tiles_held(self._sim.civ)

	def collection_people_by_tile(self) -> Dict[str, float]:
		"""People on each tile the state holds: the tracked regions' where they cover the tiles, else the nation spread by settlement."""
		tracked = self._sim.people_by_tile()
		if tracked is not None:
			return dict(tracked)
		held = self.held_tiles()
		return collection.spread_people(self._sim.population.total, settlement.population_shares(held))

	def collection_modes(self) -> List[str]:
		"""The route modes the state's held technologies open."""
		return usable_modes([self._sim.held_and_running()], self._sim.world_map)

	def collection_world_map(self) -> Any:
		return self._sim.world_map

	def arable_share(self, tiles: FrozenSet[str]) -> float:
		"""The share of the arable land the state holds that lies on `tiles`."""
		held = self.held_tiles()
		total = sum(arable_hectares(tile) for tile in held)
		return sum(arable_hectares(tile) for tile in held if tile in tiles) / total if total > 0.0 else 0.0

	def land_rent_paid_by_tile(self) -> Dict[str, float]:
		return self._sim.economy.agent_land_rent_paid_by_tile()

	def land_rent_owners(self, tiles: Optional[FrozenSet[str]] = None) -> List[Tuple[Any, float]]:
		"""(stratum, rent received) of the rent paid on `tiles` (all when none): the agent economy keeps rent with its
		household cohorts by what each owns, and the strata are slices of the cohorts ranked by income, so each
		stratum received the rent of its slice. Empty while the economy opens, when the tax is drawn from the edge."""
		curve = self._sim.economy.agent_cohort_land_rents(tiles)  # type: ignore[attr-defined]
		if not curve:
			return []
		home = [actor for actor in self._sim.actors.of_kind("stratum")  # type: ignore[attr-defined]
				if actor.record.country is None and actor.record.exited_year is None]
		received = observed_incomes(home, self, curve)
		return [(stratum, received[stratum.record.stratum]) for stratum in home if received.get(stratum.record.stratum, 0.0) > 0.0]
