"""The one affordability rule for buying things outright.

Every quote of an affordable amount and every purchase gate asks here, so a
quoted amount is always purchasable. The budget is the actor's ordinary
spending power: cash plus the share of the credit line a lender advances
against a purchase. Any actor with a household and a credit line uses it.
"""
import math

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


def refusal_text(actor, what, cost):
    """Refusal that cites the same budget the quote reports."""
    return ("cannot afford %s: it costs %s denarii and you could raise %s "
            "(cash %s, plus credit). Nothing was changed."
            % (what, "{:,.0f}".format(cost),
               "{:,.0f}".format(purchase_budget(actor)),
               "{:,.0f}".format(actor.capital)))
