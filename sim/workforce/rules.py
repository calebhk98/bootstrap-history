"""Workforce rules: plain functions of plain values."""
import math

HANDS_TOLERANCE = 1e-9      # a shortfall of hands below this is arithmetic noise, not a person missing


def surviving_people(headcount: float, survival_share: float) -> float:
	"""How many of `headcount` people survive a shock: the share of them, fractions kept (a staff is full-time equivalents,
	hours over the working year, not whole persons)."""
	return headcount * survival_share


def wage_materials_of(staple, trade_registry):
	"""The materials a wage is set against, in order: the staple, then each trade's tool materials (trades in id order),
	each material once."""
	materials = [staple]
	for trade_id in sorted(trade_registry):
		for material in trade_registry[trade_id].get("tool_basket", ()):
			if material not in materials:
				materials.append(material)
	return materials


def count_after_bleed(count, floor, bleed):
	"""A staff count after it loses the share `bleed`: it stops falling at `floor`, and a count already below the floor
	stays as it is (a bleed never hires)."""
	return min(count, max(floor, count * (1.0 - bleed)))


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


def living_cost_charged(living_cost, dependants_beyond_means, wages_paid_in_clearing):
	"""The living cost the household pays itself this year: the whole cost less the dependants the income cannot carry, less
	the staff wages the labour core's clearing pays from the household's purse (never below zero)."""
	carried = living_cost - dependants_beyond_means
	return carried - min(carried, wages_paid_in_clearing)


def market_pressure_after_a_year(pressure, kept_share, flat_fade):
	"""The pressure the household's own buying put on the people market after sellers restock: a share is kept, a flat amount fades,
	never below zero."""
	return max(0.0, pressure * kept_share - flat_fade)


def people_to_buy(capital, base_price, hands_lacking, capital_floor_in_prices, capital_per_person_in_prices):
	"""How many people the standing policy buys this year: none unless the purse holds the floor (in base prices of one person);
	then the whole people the household's shut concerns lack hands for, as many as the purse holds at the per-person reserve."""
	if capital > capital_floor_in_prices * base_price:
		return max(0, min(math.ceil(hands_lacking - HANDS_TOLERANCE), int(capital // (capital_per_person_in_prices * base_price))))
	return 0


def people_to_free(slaves, share_divisor):
	"""How many of the slaves held the standing policy frees when it fires: a share of them, at least one."""
	return max(1, slaves // share_divisor)


def opening_wage_index(civilisation):
	"""The wage index the civilisation opens on (the index is measured against it); its file states it."""
	return float(civilisation["wage_index"])
