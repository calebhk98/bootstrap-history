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
