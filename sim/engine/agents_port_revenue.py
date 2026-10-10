"""What a state asks the simulated world when it assesses revenue: its declared forms and the bases they read."""
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from sim.agents.api import observed_incomes, revenue
from sim.geography.api import arable_hectares, tiles_held


class RevenueView:
	"""Read-only questions behind a state's revenue; mixed into `SimWorld`."""

	_sim: Any

	def revenue_forms(self) -> List[Dict[str, Any]]:
		"""The forms of revenue the civilisation's state raises, as its data declares them."""
		return list(self._sim.civ.get("state_revenue") or [])

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

	def material_price(self, material: str) -> float:
		"""Money for one tonne of a material at the price the market quotes."""
		return self.material_cost(material, 1.0)  # type: ignore[attr-defined,no-any-return]

	def trade_value(self, direction: str) -> float:
		"""Money's worth of goods imported ("in") or exported ("out") in the last completed year."""
		trade = self._sim.state.economy.foreign_trade_by_year.get(str(self.year - 1), {})  # type: ignore[attr-defined]
		return float(trade.get(direction, 0.0))

	def coin_stock_value(self) -> float:
		"""Money's worth of the coin this society holds, from its coin standard."""
		return self._sim.economy.coin_stock_value()

	def held_tiles(self) -> List[str]:
		return tiles_held(self._sim.civ)

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
