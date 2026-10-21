"""What the home state decides about land and debt this year, handed to the economy as plain tiles."""
from sim.agents.api import government_levers, policy_land
from sim.economy import api as economy_api


def debt_relief_tiles(sim, economy):
    """Tiles whose households' debts the home state's policy cancels this year; none without a government."""
    government = sim.actors.government_of(None)
    if government is None:
        return ()
    return tuple(policy_land.debt_relief_tiles(government, economy_api.indebted_tiles(economy)))


def tax_rates(sim):
    """(form, rate) the home state holds this year, for the economy to collect at; none without a government."""
    government = sim.actors.government_of(None)
    if government is None:
        return ()
    return tuple((form["form"], float(form["rate"])) for form in government_levers.revenue_forms(government.record))


def farmed_forms(sim, economy):
    """Money revenue forms the home state lets to the best bidder this year."""
    government = sim.actors.government_of(None)
    if government is None:
        return ()
    return tuple(policy_land.farmed_forms(government, economy_api.money_revenue_forms(economy)))
