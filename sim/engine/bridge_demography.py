"""Bridge entries the demography module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish, asks the engine exactly as the old code did, and is never cached. Each
command applies what the yearly demographic step did inline, in the same order."""
from .bridge import bridge_view


# ---- agriculture: the farm land and the year's technique, which the farm workforce keeps on the engine ----

@bridge_view("farm_land")
def farm_land(sim):
    """The land the farm holds and its quality (the farm workforce sets it as it clears ground)."""
    return sim.farm_land


@bridge_view("farm_technique_this_year")
def farm_technique_this_year(sim):
    """The farming technique the farm workforce chose for the year."""
    return sim._farm_technique_this_year
