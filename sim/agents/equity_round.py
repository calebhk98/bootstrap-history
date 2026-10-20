"""A firm that cannot borrow what it needs to grow sells a share of its equity to the households that hold savings.

The investor is the best-placed household of a free stratum: it values a share at the present value of the
dividends the firm pays at the market rate, and pays no more than that nor more than it can spare. The deal is an exchange offer, so the shares, the money and the later dividends all move through the
same books as any other."""
from typing import Any, List

from sim.world import capital_market

from . import exchange, firm_entry, household_wealth
from .equity_need import NEED_KEY
from .registry import register_spawner
from .tuning_patent import DIVIDEND_PAYOUT_SHARE



def whole_equity_worth(firm: Any, world: Any) -> float:
	"""What the whole of the firm's equity is worth now: the present value, at the market rate, of the dividends it
	pays out of its last margin."""
	return capital_market.perpetuity_value(DIVIDEND_PAYOUT_SHARE * firm.record.last_margin, world.market_rate(),
										   capital_market.RATE_FLOOR_SHARE * world.starting_rate())


def raise_equity(registry: Any, world: Any, firm: Any) -> float:
	"""Sell the firm's equity to the best-placed investor for what it needs; the money raised."""
	need = float(firm.record.plan.pop(NEED_KEY, 0.0))
	whole = whole_equity_worth(firm, world)
	left = 1.0 - firm.record.issued
	if need <= 0.0 or whole <= 0.0 or left <= 0.0:
		return 0.0
	for investor in firm_entry.founder_candidates(registry):
		spare = household_wealth.personal_capital(investor)
		share = min(left, need / whole, spare / whole)
		price = share * whole
		if price <= 0.0:
			continue
		offered = exchange.make_offer(firm, investor, {"shares": {firm.actor_id: share}}, {"money": price}, world)
		exchange.accept(investor, offered["id"], registry.get, world)
		household_wealth.commit(investor, price)
		return price
	return 0.0


def equity_rounds(registry: Any, world: Any) -> List[str]:
	"""Yearly: every firm held back for want of credit raises equity. Founds no actors."""
	for firm in registry.active_firms():
		if firm.record.plan.get(NEED_KEY, 0.0) > 0.0:
			raise_equity(registry, world, firm)
	return []


register_spawner("equity_rounds", equity_rounds)
