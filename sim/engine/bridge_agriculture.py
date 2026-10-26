"""Bridge entries the agriculture module uses until the modules that own these facts move.

Each view answers through `Sim` as the old mixin methods did; when its owner moves it publishes the same name and the entry
is deleted. The geography ones hand the module the per-tile sums over the held land. `legacy_dice` is the game's random
source, used in place."""
from sim.assembly.api import QUOTE

from . import externalities
from .bridge import bridge_view


# ---- labour, prices, hazards and the game's own state ----

@bridge_view("externality_yield_factors", kind=QUOTE)
def externality_yield_factors(sim, year):
    """{tile: factor} the mods' externalities agree on for the year's harvest, each clamped to 0..1."""
    return externalities.yield_factors(sim, year)


@bridge_view("legacy_dice")
def legacy_dice(sim):
    """The game's random source; the weather salt is drawn from it once."""
    return sim.rng
