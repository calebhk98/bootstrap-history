"""`Firm`: an independent business that copies a proven concern and runs it.

It values only the profit it expects from a concern it can enter, and runs
the concern under the same upkeep and takings rules as the founder's, sharing
the market with every other operator.
"""
from typing import Any, Callable, List, Optional

from .base import RecordedActor
from .tuning import EXIT_LOSS_YEARS, VALUE_HORIZON_YEARS


class Firm(RecordedActor):
	kind = "firm"

	# Set by the registry: how many other operators share a concern's market.
	rivals_of: Optional[Callable[[str, str], int]] = None

	def imitation_candidates(self, world: Any) -> List[str]:
		# a firm values only the concern it is aiming at
		target = self.record.target
		return [target] if target in world.demonstrated() else []

	def imitation_worth(self, node_id: str, world: Any) -> float:
		if node_id != self.record.target:
			return 0.0
		return max(0.0, self.record.last_margin) * VALUE_HORIZON_YEARS

	def on_copied(self, node_id: str, world: Any) -> None:
		if node_id == self.record.target:
			self.concerns.add(node_id)
			self.record.opened_year[node_id] = world.year

	def staff_concern(self, node_id: str, world: Any) -> float:
		"""Take on the people running a concern needs from the shared pool; the share of
		them found, which is the share of its output that gets made."""
		found = 1.0
		for trade, wanted in sorted(world.concern_staff(node_id).items()):
			free = world.free_fte(trade, self.actor_id)
			if free is None:
				continue
			free -= self.workforce.get(trade, 0.0)
			taken = min(wanted, max(0.0, free))
			self.workforce[trade] = self.workforce.get(trade, 0.0) + taken
			found = min(found, taken / wanted)
		return found

	def operate(self, world: Any) -> None:
		for node_id in sorted(self.concerns):
			rivals = self.rivals_of(node_id, self.actor_id) if self.rivals_of else 0
			found = self.staff_concern(node_id, world)
			self.record.staffing[node_id] = found
			takings = found * world.concern_takings(node_id, self.record.opened_year[node_id], rivals)
			upkeep = world.upkeep(node_id)
			self.credit(takings, "takings")
			self.debit(upkeep, "upkeep")
			levy = world.government().collect(self, takings, world)
			margin = takings - upkeep - levy
			self.record.last_margin = margin
			self.record.loss_years = self.record.loss_years + 1 if margin < 0 else 0

	def act(self, world: Any) -> None:
		super().act(world)
		self.operate(world)
		if self.record.loss_years >= EXIT_LOSS_YEARS:
			self.concerns.clear()
			self.record.exited_year = world.year
