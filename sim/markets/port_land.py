"""What the home state decides about land and debt this year, handed to the economy as plain tiles."""
from sim.agents.api import government_levers, land_moves, policy_land, tax_burden
from sim.economy import api as economy_api

from sim.actors.api import land_decree


def debt_relief_tiles(sim, economy):
    """Tiles whose households' debts the home state's policy cancels this year; none without a government."""
    government = sim.actors.government_of(None)
    if government is None:
        return ()
    return tuple(policy_land.debt_relief_tiles(government, economy_api.indebted_tiles(economy)))


def title_moves(sim, economy):
    """(tile, giver, receiver, share) the home state decrees this year: confiscation (once, the lever is cleared) and land
    reform (while set) on the tiles it owns. The land taken off private holders is the tile's grievance (unrest.py)."""
    government = sim.actors.government_of(None)
    if government is None:
        return ()
    confiscate, cap = land_decree.decree(government)
    if confiscate <= 0.0 and cap is None:
        return ()
    held, tenancies = economy_api.title_holdings(economy, sim.tiles_owned_by(str(sim.civ["id"])))
    plan = land_moves.planned(held, tenancies, government.actor_id, confiscate, cap)
    land_decree.record_decree(government, plan)
    return tuple((tile, move.giver, move.receiver, move.share) for tile, moves in sorted(plan.items()) for move in moves)


def tax_rates(sim):
    """(form, rate) the home state holds this year, for the economy to collect at; none without a government."""
    government = sim.actors.government_of(None)
    if government is None:
        return ()
    return tuple((form["form"], float(form["rate"])) for form in government_levers.revenue_forms_of(government))


def farmed_forms(sim, economy):
    """Money revenue forms the home state lets to the best bidder this year."""
    government = sim.actors.government_of(None)
    if government is None:
        return ()
    return tuple(policy_land.farmed_forms(government, economy_api.money_revenue_forms(economy)))


def land_tax_share_of_rent(sim):
    """Share of a rent the home state's forms on land take from the owner; none without a government."""
    if sim.actors.government_of(None) is None:
        return 0.0
    return tax_burden.land_tax_share_of_rent(sim.actor_world())
