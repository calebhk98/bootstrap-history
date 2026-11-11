"""A firm grows the concerns it runs while the market's return on the added capacity beats its cost of capital."""
from typing import Any

from . import capital_structure, equity_need, equity_round, firm_entry, ledger
from .edges import EDGE_BUILDERS
from .tuning import EXPANSION_RATE


class Expansion:
	"""A firm's growth (`firm.expansion`): capacity is bought with the purse or with credit, one step a year."""

	def __init__(self, firm: Any) -> None:
		self.firm = firm

	def _added_carry(self, node_id: str, capacity: float, step: float, world: Any) -> float:
		"""What `step` more founding sizes add to the site rent and the manager's hours a plant carries whatever it sells
		(the figure `business_books.carry` pays); nothing when the country keeps no record of either."""
		tile = self.firm.location()
		before = firm_entry.carrying_cost(world, node_id, capacity, tile)
		after = firm_entry.carrying_cost(world, node_id, capacity + step, tile)
		return 0.0 if before is None or after is None else after - before

	def _equity_costs_less(self, debt_rate: float, world: Any) -> bool:
		"""Whether the shares it could sell cost the firm less each year than the debt at `debt_rate`."""
		firm = self.firm
		refused = firm.record.plan.get(capital_structure.EQUITY_REFUSED_KEY)
		equity_open = refused is None or world.setting.year - refused > 1
		return capital_structure.prefers_equity(debt_rate, equity_round.cost_of_equity(firm, world), equity_open)

	def expand(self, world: Any) -> None:
		"""Add capacity to each concern whose staff was found in full and whose added margin pays
		the rate on the money it takes: the market rate from the purse, the actor's own rate on what it borrows."""
		firm = self.firm
		if firm.record.last_margin <= 0.0:
			return
		for node_id in sorted(firm.concerns):
			if firm.holdings.staffed_share(node_id) < 1.0:
				continue
			capacity = firm.holdings.capacity_of(node_id)
			if capacity >= world.concerns.scale_ceiling(node_id):
				continue
			step = capacity * EXPANSION_RATE
			rivals = firm.rivals_of(node_id, firm.actor_id) if firm.rivals_of else 0.0
			gain = world.capacity.expansion_gain(node_id, firm.holdings.opened_year_of(node_id, world.setting.year), capacity, step, rivals)
			gain -= self._added_carry(node_id, capacity, step, world)
			cost = world.capacity.plant_cost(node_id, firm, step)
			if gain <= 0.0:
				continue
			shortfall = max(0.0, cost - max(0.0, firm.money))
			rate = world.credit.market_rate()
			if shortfall > 0.0:
				if firm.draw_limit(world, shortfall) < shortfall:
					if gain > cost * rate:
						equity_need.note_need(firm, shortfall)  # lenders will not fund it, so it raises equity
					continue
				rate = max(rate, firm.borrowing_rate(world))
				if self._equity_costs_less(rate, world):
					if gain > cost * rate:
						equity_need.note_need(firm, shortfall)  # the shares cost it less than the debt would
					continue
			if gain <= cost * rate:
				continue
			if not ledger.pay_in_full(firm, world.setting.edge(EDGE_BUILDERS), cost, "expansion"):   # the lenders turned it down after all
				continue
			firm.business.tally.set_size(node_id, capacity + step)
			if firm.on_capacity_change is not None:
				firm.on_capacity_change(firm.actor_id)
