"""A firm that cannot borrow what it needs to grow sells a share of its equity to the households that hold savings.

The investor is the best-placed household of a free stratum: it values a share at the present value of the
dividends the firm pays at the market rate, and pays no more than that nor more than it can spare. The deal is an exchange offer, so the shares, the money and the later dividends all move through the
same books as any other."""
from typing import Any, List

from sim.world import capital_market

from . import capital_structure, exchange, firm_entry, household_wealth
from .equity_need import NEED_KEY
from .tuning_patent import DIVIDEND_PAYOUT_SHARE



def whole_equity_worth(firm: Any, world: Any) -> float:
	"""What the whole of the firm's equity is worth now: the present value, at the market rate, of the dividends it
	pays out of its last margin."""
	return capital_market.perpetuity_value(DIVIDEND_PAYOUT_SHARE * firm.record.last_margin, world.credit.market_rate(),
										   capital_market.RATE_FLOOR_SHARE * world.credit.starting_rate())


def cost_of_equity(firm: Any, world: Any) -> Any:
	"""The yield the firm gives up on the shares it would sell (capital_structure.cost_of_equity)."""
	return capital_structure.cost_of_equity(DIVIDEND_PAYOUT_SHARE * firm.record.last_margin, whole_equity_worth(firm, world))


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
		firm.record.plan.pop(capital_structure.EQUITY_REFUSED_KEY, None)
		return price
	firm.record.plan[capital_structure.EQUITY_REFUSED_KEY] = world.setting.year   # no investor took the shares: the firm borrows
	return 0.0


def equity_rounds(registry: Any, world: Any) -> List[str]:
	"""Yearly: every firm held back for want of credit raises equity. Founds no actors."""
	for firm in registry.concerns.active_firms():
		if firm.record.plan.get(NEED_KEY, 0.0) > 0.0:
			raise_equity(registry, world, firm)
	return []
