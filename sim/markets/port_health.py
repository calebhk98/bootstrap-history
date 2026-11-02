"""The agent economy's health figures for a game in progress (Complaint 445), through sim/economy/diagnostics.

Part of the port. The staple is the good the hunger need's basket buys most of; metals default to the
good that backs the currency, and a caller may name others.
"""
from sim.economy.api import backing_good, health_figures, hunger_goods, opening_quantities


def staple_good(agent):
    """The good of the hunger need with the largest opening basket quantity, or None."""
    economy = agent.economy()
    goods = hunger_goods(economy)
    if not goods:
        return None
    opening = opening_quantities(economy)
    return max(goods, key=lambda good: opening.get(good, 0.0), default=None)


def health_report(agent, metals=(), staple=None):
    """{"years", "staple", "metals", "figures"} over the yearly outcomes kept since this game began."""
    economy = agent.economy()
    if not metals and backing_good(economy):
        metals = (backing_good(economy),)
    staple = staple or staple_good(agent)
    outcomes = list(agent.outcomes)
    figures = health_figures(economy, outcomes, staple, metals) if outcomes and staple else {}
    return {"years": len(outcomes), "staple": staple, "metals": list(metals), "figures": figures}
