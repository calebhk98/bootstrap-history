"""A firm grows the concerns it runs while the market's return on the added capacity beats its cost of capital."""
from typing import Any

from . import ledger
from .edges import EDGE_BUILDERS
from .tuning import EXPANSION_RATE


class ExpansionMixin:
	"""Mixed into `Firm`: capacity is bought with the purse or with credit, one step a year."""

	def expand(self, world: Any) -> None:
		"""Add capacity to each concern whose staff was found in full and whose added margin pays
		the rate on the money it takes: the market rate from the purse, the actor's own rate on what it borrows."""
		if self.record.last_margin <= 0.0:  # type: ignore[attr-defined]
			return
		for node_id in sorted(self.concerns):  # type: ignore[attr-defined]
			if self.record.staffing.get(node_id, 1.0) < 1.0:  # type: ignore[attr-defined]
				continue
			capacity = self.capacity_of(node_id)  # type: ignore[attr-defined]
			if capacity >= world.scale_ceiling(node_id):
				continue
			step = capacity * EXPANSION_RATE
			rivals = self.rivals_of(node_id, self.actor_id) if self.rivals_of else 0.0  # type: ignore[attr-defined]
			gain = world.expansion_gain(node_id, self.record.opened_year[node_id], capacity, step, rivals)  # type: ignore[attr-defined]
			cost = world.plant_cost(node_id, self, step)
			if gain <= 0.0:
				continue
			shortfall = max(0.0, cost - max(0.0, self.money))  # type: ignore[attr-defined]
			rate = world.market_rate()
			if shortfall > 0.0:
				if shortfall > self.credit_ceiling(world) - self.debt():  # type: ignore[attr-defined]
					continue
				rate = max(rate, self.borrowing_rate(world))  # type: ignore[attr-defined]
			if gain <= cost * rate:
				continue
			ledger.transfer(self, world.edge(EDGE_BUILDERS), cost, "expansion")
			self.record.capacity[node_id] = capacity + step  # type: ignore[attr-defined]
			if self.on_capacity_change is not None:  # type: ignore[attr-defined]
				self.on_capacity_change(self.actor_id)  # type: ignore[attr-defined]
