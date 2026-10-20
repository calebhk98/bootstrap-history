"""What the home state decides about land and debt this year, handed to the economy as plain tiles."""
from sim.agents.api import policy_land
from sim.economy import api as economy_api


def debt_relief_tiles(sim, economy):
    """Tiles whose households' debts the home state's policy cancels this year; none without a government."""
    government = sim.actors.government_of(None)
    if government is None:
        return ()
    return tuple(policy_land.debt_relief_tiles(government, economy_api.indebted_tiles(economy)))
