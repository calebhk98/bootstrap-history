"""A firm grows the concerns it runs while the market's return on the added capacity beats its cost of capital."""
from typing import Any

from . import equity_need, firm_entry, ledger
from .edges import EDGE_BUILDERS
from .tuning import EXPANSION_RATE


class ExpansionMixin:
	"""Mixed into `Firm`: capacity is bought with the purse or with credit, one step a year."""

	def _added_carry(self, node_id: str, capacity: float, step: float, world: Any) -> float:
		"""What `step` more founding sizes add to the site rent and the manager's hours a plant carries whatever it sells
		(the figure `business_books.carry` pays); nothing when the country keeps no record of either."""
		tile = self.location()  # type: ignore[attr-defined]
		before = firm_entry.carrying_cost(world, node_id, capacity, tile)
		after = firm_entry.carrying_cost(world, node_id, capacity + step, tile)
		return 0.0 if before is None or after is None else after - before

	def expand(self, world: Any) -> None:
		"""Add capacity to each concern whose staff was found in full and whose added margin pays
		the rate on the money it takes: the market rate from the purse, the actor's own rate on what it borrows."""
		if self.record.last_margin <= 0.0:  # type: ignore[attr-defined]
			return
		for node_id in sorted(self.concerns):  # type: ignore[attr-defined]
			if self.staffed_share(node_id) < 1.0:  # type: ignore[attr-defined]
				continue
			capacity = self.capacity_of(node_id)  # type: ignore[attr-defined]
			if capacity >= world.scale_ceiling(node_id):
				continue
			step = capacity * EXPANSION_RATE
			rivals = self.rivals_of(node_id, self.actor_id) if self.rivals_of else 0.0  # type: ignore[attr-defined]
			gain = world.expansion_gain(node_id, self.opened_year_of(node_id, world.year), capacity, step, rivals)  # type: ignore[attr-defined]
			gain -= self._added_carry(node_id, capacity, step, world)
			cost = world.plant_cost(node_id, self, step)
			if gain <= 0.0:
				continue
			shortfall = max(0.0, cost - max(0.0, self.money))  # type: ignore[attr-defined]
			rate = world.market_rate()
			if shortfall > 0.0:
				if shortfall > self.credit_ceiling(world) - self.debt():  # type: ignore[attr-defined]
					if gain > cost * rate:
						equity_need.note_need(self, shortfall)  # lenders will not fund it, so it raises equity
					continue
				rate = max(rate, self.borrowing_rate(world))  # type: ignore[attr-defined]
			if gain <= cost * rate:
				continue
			ledger.transfer(self, world.edge(EDGE_BUILDERS), cost, "expansion")
			self.business.set_size(node_id, capacity + step)  # type: ignore[attr-defined]
			if self.on_capacity_change is not None:  # type: ignore[attr-defined]
				self.on_capacity_change(self.actor_id)  # type: ignore[attr-defined]
