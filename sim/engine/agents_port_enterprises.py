"""What a state's own plants ask of the world: the inputs a plant uses up in a year."""
import math
from typing import Any, Callable, Dict, Optional

from sim.agents.api import business_plant_books
from sim.unit_conversions import KILOGRAMS_PER_TONNE

from .economy_port_setup import unit_mass_kg
from .node_revenue_market import basket_market_factor


class EnterpriseView:
	"""Read-only questions behind a state's plants; mixed into `SimWorld`."""

	_sim: Any

	def concern_inputs(self, node_id: str) -> Dict[str, float]:
		"""Tonnes of each material a concern of the node uses up in a year at its founding size, from its production
		entries; empty for a node whose figures are not derived from output."""
		baskets = self._sim.concern_baskets_now(node_id)
		if baskets is None:
			return {}
		inputs = {}
		for material, units in baskets.purchases.items():
			kilograms = unit_mass_kg(material)
			if units > 0.0 and math.isfinite(kilograms):
				inputs[material] = units * kilograms / KILOGRAMS_PER_TONNE
		return inputs

	# ---- the tree's figures a plant in another country is booked from (agents/business_plant_books.py)
	def book_takings(self, node_id: str, opened_year: int) -> float:
		"""Yearly takings of one founding size of a concern at its ramp, in the tree's book coin: no cost scale, no hazard factor."""
		return business_plant_books.book_takings(self._sim, node_id, self.ramp(opened_year, node_id))  # type: ignore[attr-defined]

	def book_upkeep(self, node_id: str) -> float:
		"""Yearly upkeep of one founding size of a concern without its crew's pay, in the tree's book coin."""
		return business_plant_books.book_upkeep(self._sim, node_id)

	def market_factor_at(self, node_id: str, unit_price: Callable[[str], Optional[float]]) -> float:
		"""A concern's market over its long-run prices at the prices `unit_price` quotes (money per unit); one for a concern
		whose takings are not derived from output or whose goods `unit_price` quotes none of."""
		baskets = self._sim.concern_baskets_now(node_id)
		if baskets is None or any(unit_price(material) is None for material in baskets.outputs):
			return 1.0
		return float(basket_market_factor(baskets.outputs, baskets.purchases, self._sim._material_prices(), unit_price))

	def in_goods_category(self, node_id: str) -> bool:
		"""Whether the concern sells into a goods category, whose demand the home society's households set."""
		return self.nodes[node_id].get("cat") in self._sim.GOODS_CATEGORIES  # type: ignore[attr-defined,no-any-return]

	def plant_books(self, node_id: str, opened_year: int, rivals: float, size: float) -> Any:
		"""Takings, upkeep and wages of a plant in the home economy."""
		return business_plant_books.home_books(self, node_id, opened_year, rivals, size)
