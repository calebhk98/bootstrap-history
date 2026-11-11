"""The labour a state's masonry works take: the hours of the laid-wall recipe, by trade, per square metre of public building.

The recipe is production data (the service named in `data/world/state_masonry.json`), so the state's works draw the
same masons and labourers, at the same hours, as a household's shelter does. A trade the country has nobody in is done
by the builder role's trade instead."""
from typing import Any, Dict, Mapping

from sim.world import state_masonry

from .tuning_spending import MASONRY_WALL_M3_PER_M2

BUILDER_ROLE = "builder"


def person_years_by_trade(world: Any) -> Dict[str, float]:
	"""Person-years of each trade to raise one square metre of public building."""
	hours = world.enterprises.recipe_labour_hours(state_masonry.service_material())
	by_trade = state_masonry.person_years_per_square_metre(hours, MASONRY_WALL_M3_PER_M2, world.labour.hours_per_person_year)
	exists = {trade: world.labour.trade_exists(trade) for trade in by_trade}
	return state_masonry.fold_absent_trades(by_trade, exists, world.labour.trade_of_role(BUILDER_ROLE))


def person_years_total(world: Any) -> float:
	"""Person-years, all trades together, to raise one square metre."""
	return sum(person_years_by_trade(world).values())


def wage_cost_per_square_metre(world: Any) -> float:
	"""Wages of the crew that raises one square metre, at each trade's pay."""
	return sum(years * world.labour.pay_per_person_year(trade) for trade, years in person_years_by_trade(world).items())


def square_metres_raisable(gap: float, money: float, crew_per_m2: Mapping[str, float], wage: Mapping[str, float],
						   people_cap: Mapping[str, float]) -> float:
	"""Square metres the state can raise this year: no more than the gap, than `money` pays at each trade's wage, or than
	the people it may take from each trade allow."""
	cost = sum(years * wage[trade] for trade, years in crew_per_m2.items())
	limits = [gap]
	if cost > 0.0:
		limits.append(money / cost)
	limits.extend(people_cap[trade] / years for trade, years in crew_per_m2.items() if years > 0.0)
	return max(0.0, min(limits))
