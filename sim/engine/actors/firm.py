"""`Firm`: an independent business that copies a proven concern and runs it.

It values only the profit it expects from a concern it can enter, and runs
the concern under the same upkeep and takings rules as the founder's, sharing
the market with every other operator.
"""
from typing import Any, Callable, Optional

from .base import RecordedActor
from .tuning import EXIT_LOSS_YEARS, VALUE_HORIZON_YEARS


class Firm(RecordedActor):
	kind = "firm"

	# Set by the registry: how many other operators share a concern's market.
	rivals_of: Optional[Callable[[str, str], int]] = None

	def imitation_worth(self, node_id: str, world: Any) -> float:
		if node_id != self.record.target:
			return 0.0
		return max(0.0, self.record.last_margin) * VALUE_HORIZON_YEARS

	def on_copied(self, node_id: str, world: Any) -> None:
		if node_id == self.record.target:
			self.concerns.add(node_id)
			self.record.opened_year[node_id] = world.year

	def operate(self, world: Any) -> None:
		for node_id in sorted(self.concerns):
			rivals = self.rivals_of(node_id, self.actor_id) if self.rivals_of else 0
			takings = world.concern_takings(node_id, self.record.opened_year[node_id]) / (1.0 + rivals)
			upkeep = world.upkeep(node_id)
			margin = takings - upkeep
			self.credit(takings, "takings")
			self.debit(upkeep, "upkeep")
			self.record.last_margin = margin
			self.record.loss_years = self.record.loss_years + 1 if margin < 0 else 0

	def advance(self, world: Any) -> None:
		super().advance(world)
		self.operate(world)
		if self.record.loss_years >= EXIT_LOSS_YEARS:
			self.concerns.clear()
			self.record.exited_year = world.year
