"""What it is worth to a firm to run a concern at a larger size: the view behind its expansion."""
from typing import Any

from sim.agents.api import MANAGEMENT_SPAN_EXPONENT, imitation


class CapacityView:
	"""Read-only questions about growing a concern; mixed into `ActorWorld`."""

	needs: Any

	def span_factor(self, capacity: float) -> float:
		"""Wages of a concern at `capacity` times its founding size, over one founding-size wage bill."""
		return capacity ** (1.0 + MANAGEMENT_SPAN_EXPONENT)

	def running_cost(self, node_id: str, capacity: float) -> float:
		"""Yearly upkeep and wages of a concern run at `capacity` times its founding size."""
		return self.upkeep(node_id, capacity) + self.concern_wage_bill(node_id, capacity)  # type: ignore[attr-defined]

	def expansion_gain(self, node_id: str, opened_year: int, capacity: float, step: float, rivals: float) -> float:
		"""Yearly margin gained by growing a concern from `capacity` to `capacity + step`: the takings
		at the price the larger supply leaves, less the upkeep and wages of the added size."""
		needs = self.needs
		base = needs.concern_takings(node_id, self.ramp(opened_year, node_id))  # type: ignore[attr-defined]
		category = self.nodes[node_id].get("cat")  # type: ignore[attr-defined]
		if category in self.goods_category_names:  # type: ignore[attr-defined]
			before = capacity * base * needs.goods_category_factor(category)
			after = (capacity + step) * base * needs.goods_category_factor_with_entrants(category, step)
		else:
			before = base * capacity / (capacity + rivals)
			after = base * (capacity + step) / (capacity + step + rivals)
		return (after - before) - (self.running_cost(node_id, capacity + step) - self.running_cost(node_id, capacity))

	def plant_cost(self, node_id: str, actor: Any, step: float) -> float:
		"""Money for `step` founding sizes more of a concern's plant, for an actor that already knows how."""
		plan = imitation.copy_plan(actor, [node_id], self)
		return float(plan["total"]) * step
