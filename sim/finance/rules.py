"""The finance module's rules as plain functions of their inputs: credit ceilings, what arrears cost, what a state lends."""
from .constants import LENDABLE_RESERVE_SHARE


def calculate_credit_ceiling(raw_credit, running_cost_floor, serviceable, price_index=1.0, market_cap=None):
	"""The nominal borrowing ceiling. `market_cap` is what lenders can still advance (in the same units as the other
	figures); None before the market has met."""
	limit = min(raw_credit, serviceable)
	if market_cap is not None:
		limit = min(limit, market_cap)
	return max(limit, running_cost_floor) * price_index


def bearable_part(amount, capital, credit_limit_after):
	"""How much of `amount` a purse of `capital` and a credit line of `credit_limit_after` (read at the capital left
	after paying) can take without capital ending below the negative of the limit."""
	return min(amount, max(0.0, capital + credit_limit_after))


def interest_on_arrears(capital, rate):
	"""The yearly interest on a debt: nothing while the purse is in credit."""
	return max(0.0, -capital) * rate


def net_after_interest(net_before_interest, capital, rate):
	"""Recurring net once the interest on any debt is counted as the cost it is."""
	return net_before_interest - interest_on_arrears(capital, rate)


def dependants_not_carried(dependants, surplus, creditors_share):
	"""The part of the dependants' cost the income cannot carry: what the surplus leaves after the creditors' share,
	never more than the dependants cost and never less than nothing."""
	carried = surplus * (1.0 - creditors_share)
	return dependants - min(dependants, max(0.0, carried))


def dependants_beyond_means_of(capital, dependants, living, revenue, upkeep, mine_cost, debt_rate, creditors_share_in_arrears):
	"""The part of the dependants' cost a household cannot carry: what its income leaves after upkeep, mine costs, the rest
	of its living cost and the interest on any arrears. A household with savings keeps all that surplus for its dependants;
	one in arrears also pays its creditors their share of it first."""
	interest = interest_on_arrears(capital, debt_rate)
	surplus = revenue - upkeep - mine_cost - (living - dependants) - interest
	creditors_share = creditors_share_in_arrears if capital < 0 else 0.0
	return dependants_not_carried(dependants, surplus, creditors_share)


def state_spare_reserve(money, standing_need, cannot_meet_own_need):
	"""What a state holds beyond its standing need; none while it cannot meet that need."""
	return 0.0 if cannot_meet_own_need else max(0.0, money - standing_need)


def lendable_share_of_reserve(spare):
	"""The part of a state's spare reserve it offers on the loanable market."""
	return LENDABLE_RESERVE_SHARE * spare


def bondage_repayment(hours_per_year, labour_share, wage_markup, labourer_hour_quote):
	"""What a year of the debtor's hours repays: the share of his hours that belong to the creditor, at the
	market's labourer hour and a markup."""
	return hours_per_year * labour_share * wage_markup * labourer_hour_quote


def serve_bondage_year(years_left, debt, repayment):
	"""(years left, debt, whether the term ended this year) after one year of service. A debt repaid early ends the
	term; a term that runs out discharges the debt that is left."""
	years_left -= 1
	debt = max(0.0, debt - repayment)
	if debt <= 0 and years_left > 0:
		years_left = 0
	if years_left <= 0:
		return 0.0, 0.0, True
	return years_left, debt, False


def living_cost_total(base, dependants, tax, status, wages):
	"""A household's yearly living cost: its own needs, its dependants', tax, appearances and the payroll."""
	return base + dependants + tax + status + wages
