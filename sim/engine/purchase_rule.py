"""The one affordability rule for buying things outright.

Every quote of an affordable amount and every purchase gate asks here, so a
quoted amount is always purchasable. The budget is the actor's ordinary
spending power: cash plus the share of the credit line a lender advances
against a purchase. Any actor with a household and a credit line uses it.
"""
import math

from sim.engine import cash_remedies

BUDGET_KIND = "buy"
# Tolerance for float noise when a cost is exactly the budget.
_EPSILON = 1e-9


def purchase_budget(actor):
    """Most the actor can spend on one outright purchase right now."""
    return actor.spending_power(BUDGET_KIND)


def can_pay(actor, cost):
    """True when the cost fits inside the purchase budget."""
    return cost <= purchase_budget(actor) + _EPSILON


def affordable_units(actor, unit_cost, decimals=1):
    """Units the budget buys, rounded down so the quoted figure is buyable."""
    scale = 10 ** decimals
    units = purchase_budget(actor) / max(unit_cost, 1e-9)
    return math.floor(units * scale + _EPSILON) / scale


def afford_means():
    """Player-facing statement of what the budget counts."""
    return "cash plus the share of your credit line a lender advances against a purchase"


def remedies_text(actor):
    """The commands that raise cash or cut costs, or an empty string."""
    lines = cash_remedies.cash_remedies(actor)
    return (" To raise cash: " + "; ".join(lines) + ".") if lines else ""


def refusal_text(actor, what, cost):
    """Refusal that states the rule, the budget, the amount short and the
    commands that raise cash."""
    budget = purchase_budget(actor)
    short = max(0.0, cost - budget)
    share = actor.SPENDING_DRAW_SHARE_ORDINARY
    return ("cannot afford %s: it costs %s denarii and you could raise %s, "
            "so you are %s short. The rule: %s (cash %s, %d%% of your credit "
            "line of %s, net of any debt). Earning or paying down %s "
            "would allow it.%s Nothing was changed."
            % (what, "{:,.0f}".format(cost), "{:,.0f}".format(budget),
               "{:,.0f}".format(short), afford_means(),
               "{:,.0f}".format(actor.capital), round(share * 100),
               "{:,.0f}".format(actor.credit_limit()), "{:,.0f}".format(short),
               remedies_text(actor)))
