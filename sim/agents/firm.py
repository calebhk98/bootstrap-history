"""`Firm`: an independent business that copies a proven concern and runs it.

It values only the profit it expects from a concern it can enter, and runs
the concern under the same upkeep and takings rules as the founder's, sharing
the market with every other operator.
"""
from typing import Any, Callable, List, Optional

from .base import RecordedActor
from .firm_expansion import ExpansionMixin
from .borrowing import TRACK_RECORD_YEARS
from .tuning import EXIT_LOSS_YEARS, VALUE_HORIZON_YEARS


class Firm(ExpansionMixin, RecordedActor):
	kind = "firm"
	borrows_for_copies = True

	# Set by the registry: how many other operators share a concern's market.
	rivals_of: Optional[Callable[[str, str], float]] = None
	# Set by the registry: told when a firm changes the size it runs a concern at.
	on_capacity_change: Optional[Callable[[], None]] = None

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

	def accept_licence(self, node_id: str, chain: List[str], world: Any) -> None:
		"""A licensed concern becomes the firm's own business."""
		self.learn(chain, world)
		self.concerns.add(node_id)
		self.record.opened_year[node_id] = world.year

	def staff_concern(self, node_id: str, world: Any) -> float:
		"""Take on the people running a concern needs from the shared pool; the share of
		them found, which is the share of its output that gets made."""
		found = 1.0
		capacity = self.capacity_of(node_id)
		for trade, wanted in sorted(world.concern_staff(node_id).items()):
			wanted *= capacity
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
			rivals = self.rivals_of(node_id, self.actor_id) if self.rivals_of else 0.0
			capacity = self.capacity_of(node_id)
			found = self.staff_concern(node_id, world)
			self.record.staffing[node_id] = found
			takings = found * world.concern_takings(node_id, self.record.opened_year[node_id], rivals, capacity)
			upkeep = world.upkeep(node_id, capacity)
			wages = found * world.concern_wage_bill(node_id, capacity)
			self.credit(takings, "takings")
			self.debit(upkeep, "upkeep")
			self.debit(wages, "wages")
			levy = world.government().collect(self, takings, world)
			royalty = world.collect_royalty(self, node_id, takings)
			margin = takings - upkeep - wages - levy - royalty
			self.record.last_margin = margin
			self.record.loss_years = self.record.loss_years + 1 if margin < 0 else 0

	def credit_earning(self, world: Any) -> float:
		return max(0.0, self.record.last_margin)

	def credit_standing(self, world: Any) -> float:
		"""A firm is trusted as its record lengthens, and not at all while it runs at a loss."""
		if self.record.loss_years > 0 or self.record.founded_year is None:
			return 0.0
		return min(1.0, max(0.0, world.year - self.record.founded_year) / TRACK_RECORD_YEARS)

	def act(self, world: Any) -> None:
		self.pay_interest(world)
		super().act(world)
		self.operate(world)
		if self.record.loss_years >= EXIT_LOSS_YEARS:
			self.concerns.clear()
			self.record.capacity.clear()
			self.record.exited_year = world.year
		else:
			self.expand(world)
