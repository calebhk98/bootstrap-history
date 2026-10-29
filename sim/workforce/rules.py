"""Workforce rules: plain functions of plain values."""


def surviving_people(dice, headcount: float, survival_share: float) -> float:
	"""How many of `headcount` people survive a shock: each is rolled one by one against `survival_share`, so headcounts
	stay whole. `dice` is the game's random source."""
	people = int(round(headcount))
	return float(sum(1 for _ in range(people) if dice.random() >= 1.0 - survival_share))


def wage_index_of(base_index, scarcity_elasticity, population_scale, unshocked_scale):
	"""The base index raised in proportion to the shortfall of the population scale below its unshocked trend."""
	shortfall = max(0.0, 1.0 - population_scale / unshocked_scale)
	return base_index * (1.0 + scarcity_elasticity * shortfall)


def extra_lit_hours(works):
	"""Hours a day that lit works add: `works` are (extra hours a day, share of the people covered)."""
	total = 0.0
	for hours, share in works:
		total += hours * share
	return total


def working_hours_per_year(convention_hours, extra_hours_per_day, base_day_hours):
	"""Hours one person gives in a year: the convention stretched in proportion to the lit hours added to a day."""
	return convention_hours * (1.0 + extra_hours_per_day / base_day_hours)


def work_order_shortfall(directive_hours, already_sold):
	"""The hours a standing work order still has to sell this year: the directive less what was already sold by
	hand, so the order tops up and never sells the same hours twice; never negative."""
	return max(0.0, directive_hours - already_sold)


def price_of_labour_hours(hours, money_per_labour_hour, price_index):
	"""What a cost declared in labour hours is now: the hours in the coin of the civilisation, at its price level."""
	return hours * money_per_labour_hour * price_index


def dependant_people(kin_and_retainers, freedmen, slaves):
	"""People the household keeps besides the founder: the kin and retainers it arrived with, and its freedmen and slaves."""
	return kin_and_retainers + freedmen + slaves


def living_cost_charged(living_cost, dependants_beyond_means, wages_prepaid):
	"""The living cost to pay this year: the whole cost less the dependants the income cannot carry, less the wages already
	paid in advance (never below zero for the advance: an advance larger than the cost nets it to zero)."""
	carried = living_cost - dependants_beyond_means
	return carried - min(carried, wages_prepaid)


def market_pressure_after_a_year(pressure, kept_share, flat_fade):
	"""The pressure the household's own buying put on the people market after sellers restock: a share is kept, a flat amount fades,
	never below zero."""
	return max(0.0, pressure * kept_share - flat_fade)


def people_to_buy(capital, base_price, artisans, capital_floor_in_prices, capital_per_person_in_prices, artisan_ceiling, most_per_year):
	"""How many people the standing policy buys this year: none unless the purse holds the floor (in base prices of one person) and
	the artisans are under the ceiling; then as many as the purse holds at the per-person reserve, at most `most_per_year`."""
	if capital > capital_floor_in_prices * base_price and artisans < artisan_ceiling:
		return min(most_per_year, int(capital // (capital_per_person_in_prices * base_price)))
	return 0


def people_to_free(slaves, share_divisor):
	"""How many of the slaves held the standing policy frees when it fires: a share of them, at least one."""
	return max(1, slaves // share_divisor)


def opening_wage_index(civilisation):
	"""The wage index the civilisation opens on (the index is measured against it); one when the file names none."""
	return float(civilisation.get("wage_index", 1.0))
