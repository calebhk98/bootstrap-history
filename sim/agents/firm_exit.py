"""A firm leaves when its concerns cannot carry it: at a loss, or earning less than their plant would lend for."""
from typing import Any

from . import household_wealth, ledger


def earns_less_than_plant_would_lend_for(firm: Any, world: Any) -> bool:
	"""Whether the margin of a firm past its first years is below the market's return on what its plant costs to build."""
	if firm.record.last_margin <= 0.0:
		return False  # a loss is counted already
	plant = 0.0
	for node_id in firm.concerns:
		if world.ramp(firm.opened_year_of(node_id, world.year), node_id) < 1.0:
			return False  # still ramping up: the industry's depth sets how long that takes
		plant += world.plant_cost(node_id, firm, firm.capacity_of(node_id))
	return firm.record.last_margin <= plant * world.market_rate()


def close_firm(firm: Any, world: Any) -> None:
	"""Stop running every concern; what is left in the purse goes back to the founder who put it up."""
	founder = firm.find_actor(firm.record.plan.get("backer", "")) if firm.find_actor is not None else None
	if founder is not None and firm.money > 0.0:
		ledger.transfer(firm, founder, firm.money, "founding stake returned")
	if founder is not None and "founder_household" in firm.record.plan:
		household_wealth.release(founder, int(firm.record.plan["founder_household"]), float(firm.record.plan.get("stake", 0.0)))
	firm.concerns.clear()
	firm.record.capacity.clear()
	firm.record.exited_year = world.year
