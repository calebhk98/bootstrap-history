"""The agent economy's health figures for a game in progress (Complaint 445), through sim/economy/diagnostics.

Part of the port. The staple is the good the hunger need's basket buys most of; metals default to the
good that backs the currency, and a caller may name others.
"""
from sim.economy.api import diagnostics, opening_quantities


def staple_good(agent):
    """The good of the hunger need with the largest opening basket quantity, or None."""
    economy = agent.economy()
    setup = economy.setup
    need = next((spec for spec in setup.basket.needs if spec.need_id == setup.hunger_need), None)
    if need is None:
        return None
    opening = opening_quantities(economy)
    goods = [good for good, _effect in need.goods]
    return max(goods, key=lambda good: opening.get(good, 0.0), default=None)


def health_report(agent, metals=(), staple=None):
    """{"years", "staple", "metals", "figures"} over the yearly outcomes kept since this game began."""
    economy = agent.economy()
    setup = economy.setup
    if not metals and setup.currency.backing_good:
        metals = (setup.currency.backing_good,)
    staple = staple or staple_good(agent)
    outcomes = list(agent.outcomes)
    figures = diagnostics.summary(outcomes, setup, staple, metals) if outcomes and staple else {}
    return {"years": len(outcomes), "staple": staple, "metals": list(metals), "figures": figures}
