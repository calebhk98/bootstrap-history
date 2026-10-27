"""The one affordability rule for buying things outright, as plain functions of the budget.

Every quote of an affordable amount and every purchase gate asks the module's views built on these, so a quoted amount is always
purchasable. The budget is the actor's ordinary spending power: cash plus the share of the credit line a lender advances against a
purchase."""
import math
from typing import Callable

from sim.refusal import Refusal

BUDGET_KIND = "buy"
EPSILON = 1e-9   # tolerance for float noise when a cost is exactly the budget


def can_pay(cost: float, budget: float) -> bool:
	"""True when the cost fits inside the purchase budget."""
	return cost <= budget + EPSILON


def affordable_units(budget: float, unit_cost: float, decimals: int = 1) -> float:
	"""Units the budget buys, rounded down so the quoted figure is buyable."""
	scale = 10 ** decimals
	unit_cost = max(unit_cost, 1e-9)
	units = budget / unit_cost
	rounded = math.floor(units * scale + EPSILON) / scale
	# the float-noise allowance must not round a figure up past what the budget pays
	return rounded if rounded * unit_cost <= budget + EPSILON else math.floor(units * scale) / scale


def affordable_whole_units(budget: float, base_unit_cost: float, cost_of_units: Callable[[float], float], steps: int = 20) -> int:
	"""Whole units whose bill `cost_of_units(n)` (rising with n) the budget covers, found by bisection from the most the base unit
	cost allows."""
	lower, upper = 0.0, budget / max(base_unit_cost, 1e-9)
	affordable = 0.0
	for _ in range(steps):
		middle = (lower + upper) / 2.0
		if cost_of_units(middle) <= budget:
			affordable = middle
			lower = middle
		else:
			upper = middle
	return int(affordable)


def afford_means() -> str:
	"""Player-facing statement of what the budget counts."""
	return "cash plus the share of your credit line a lender advances against a purchase"


def remedies_sentence(lines) -> str:
	"""The commands that raise cash or cut costs as a sentence, or an empty string."""
	return (" To raise cash: " + "; ".join(lines) + ".") if lines else ""


def cash_short(what: str, cost: float, budget: float, share: float, capital_text: str, cost_text: str, budget_text: str,
               short_text: str, limit_text: str, remedies: str) -> Refusal:
	"""The refusal that states the rule, the budget, the amount short and the commands that raise cash."""
	short = max(0.0, cost - budget)
	return Refusal("cash_short", "cannot afford %s: it costs %s and you could raise %s, "
	               "so you are %s short. The rule: %s (cash %s, %d%% of your credit "
	               "line of %s, net of any debt). Earning or paying down %s "
	               "would allow it.%s Nothing was changed."
	               % (what, cost_text, budget_text, short_text, afford_means(), capital_text, round(share * 100), limit_text,
	                  short_text, remedies), cost=cost, budget=budget, short=short)
