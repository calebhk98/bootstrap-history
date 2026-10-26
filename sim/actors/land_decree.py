"""The home government's land decree, read from and written to its record; kept apart from `economy_port_land.py`, which
never reads a government's record."""
from sim.agents.api import government_levers_land, land_moves


def decree(government):
    """(share of private land to confiscate, reform cap or None) the government's levers ask for."""
    record = government.record
    return government_levers_land.confiscation_share(record), government_levers_land.reform_cap(record)


def record_decree(government, plan):
    """Clear the once-only confiscation lever and book the land taken off private holders as the tile's grievance."""
    record = government.record
    record.levers.pop(government_levers_land.CONFISCATION, None)
    for tile, moves in plan.items():
        taken = land_moves.taken_from_private(moves, government.actor_id)
        if taken > 0.0:
            record.land_taken_by_tile[tile] = min(1.0, record.land_taken_by_tile.get(tile, 0.0) + taken)
