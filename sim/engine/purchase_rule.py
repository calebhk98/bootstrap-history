"""The one affordability rule for buying things outright, asked with the game in hand.

The rule and its budget are the finance module's (`sim/finance/purchase_rules.py`, and the views `purchase_budget`, `can_pay`,
`affordable_units`, `purchase_refusal`); the screens and the gates that still hold the game ask them here. Each line goes when
its last caller reads the view itself."""
from sim.finance.api import purchase_rules

affordable_whole_units = purchase_rules.affordable_whole_units
afford_means = purchase_rules.afford_means


def purchase_budget(actor):
    """Most the actor can spend on one outright purchase right now."""
    return actor.view("purchase_budget")()


def can_pay(actor, cost):
    """True when the cost fits inside the purchase budget."""
    return actor.view("can_pay")(cost)


def affordable_units(actor, unit_cost, decimals=1):
    """Units the budget buys, rounded down so the quoted figure is buyable."""
    return actor.view("affordable_units")(unit_cost, decimals)


def remedies_text(actor):
    """The commands that raise cash or cut costs, or an empty string."""
    return actor.view("purchase_remedies_text")()


def refusal_text(actor, what, cost):
    """Refusal that states the rule, the budget, the amount short and the commands that raise cash."""
    return actor.view("purchase_refusal")(what, cost)
