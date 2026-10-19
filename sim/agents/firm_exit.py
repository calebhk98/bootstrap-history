"""A firm leaves when its concerns cannot carry it: at a loss, earning less than their plant would lend for, or
owing interest that outruns its margin."""
from typing import Any

from . import business_books, household_wealth, ledger


def earns_less_than_plant_would_lend_for(firm: Any, world: Any) -> bool:
	"""Whether the margin of a firm past its first years is below the market's return on what its plant costs to build."""
	if firm.record.last_margin <= 0.0:
		return False  # a loss is counted already
	plant = 0.0
	for node_id in firm.concerns:
		if business_books.ramp(firm.business, node_id, world) < 1.0:
			return False  # still ramping up: the industry's depth sets how long that takes
		plant += world.plant_cost(node_id, firm, firm.capacity_of(node_id))
	return firm.record.last_margin <= plant * world.market_rate()


def interest_outruns_margin(firm: Any, interest: float, world: Any) -> bool:
	"""Whether a firm past its first years owes interest this year at least as large as its margin, so its debt
	only grows: a firm that can never pay down what it owes is not a going concern."""
	if interest <= 0.0 or firm.record.last_margin <= 0.0:
		return False  # no debt, or a loss counted already
	if business_books.any_ramping(firm.business, world):
		return False  # still ramping up: its margin has not reached what the concern will earn
	return firm.record.last_margin <= interest


def close_firm(firm: Any, world: Any) -> None:
	"""Stop running every concern. Creditors come first: the purse repays the claims against the firm, what is
left goes back to the founder who put it up, and any debt still unpaid is written off."""
	founder = firm.find_actor(firm.record.plan.get("backer", "")) if firm.find_actor is not None else None
	firm.purses.repay_from_purse(firm.account_id)
	if founder is not None and firm.money > 0.0:  # money is net of debt, so this is only cash left after every claim
		ledger.transfer(firm, founder, firm.money, "founding stake returned")
	if founder is not None and "founder_household" in firm.record.plan:
		household_wealth.release(founder, int(firm.record.plan["founder_household"]), float(firm.record.plan.get("stake", 0.0)))
	firm.write_off_debt()  # what it still owes is lost to its lenders: nothing is left to repay it from
	firm.business.close_all()
	firm.record.exited_year = world.year
