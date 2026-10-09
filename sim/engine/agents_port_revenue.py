"""What a state asks the simulated world when it assesses revenue: its declared forms and the bases they read."""
from typing import Any, Dict, List, Tuple

from sim.agents.api import revenue


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

	def land_rent_paid_by_tile(self) -> Dict[str, float]:
		return self._sim.economy.agent_land_rent_paid_by_tile()

	def land_rent_owners(self) -> List[Tuple[Any, float]]:
		"""The agent economy keeps rent with its household cohorts, not with the strata, so no payer is named and
		the tax is drawn from the edge (taxpayers outside the modelled actors)."""
		return []
