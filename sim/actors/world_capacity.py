"""What it is worth to a firm to run a concern at a larger size: the view behind its expansion."""
from typing import Any

from sim.agents.api import MANAGEMENT_SPAN_EXPONENT, imitation


class Capacity:
	"""Read-only questions about growing a concern. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world

	@property
	def needs(self) -> Any:
		return self.world.needs

	def span_factor(self, capacity: float) -> float:
		"""Wages of a concern at `capacity` times its founding size, over one founding-size wage bill."""
		return capacity ** (1.0 + MANAGEMENT_SPAN_EXPONENT)

	def running_cost(self, node_id: str, capacity: float) -> float:
		"""Yearly upkeep and wages of a concern run at `capacity` times its founding size."""
		concerns = self.world.concerns
		return concerns.upkeep(node_id, capacity) + concerns.concern_wage_bill(node_id, capacity)

	def expansion_gain(self, node_id: str, opened_year: int, capacity: float, step: float, rivals: float) -> float:
		"""Yearly margin gained by growing a concern from `capacity` to `capacity + step`: the takings
		at the price the larger supply leaves, less the upkeep and wages of the added size."""
		needs = self.needs
		base = (needs.concern_takings(node_id, self.world.concerns.ramp(opened_year, node_id))
		        * needs.node_output_market_factor(self.world.setting.nodes[node_id]))
		before = base * capacity / (capacity + rivals)
		after = base * (capacity + step) / (capacity + step + rivals)
		return (after - before) - (self.running_cost(node_id, capacity + step) - self.running_cost(node_id, capacity))

	def plant_cost(self, node_id: str, actor: Any, step: float) -> float:
		"""Money for `step` founding sizes more of a concern's plant, for an actor that already knows how."""
		plan = imitation.copy_plan(actor, [node_id], self.world)
		return float(plan["total"]) * step
