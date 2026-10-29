"""Bridge entries the workforce module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
labour adapter did, and is never cached. The `legacy_*` views are raw state the module still reads or writes in place;
they go when that state moves."""
from .bridge import bridge_view


# ---- the founder, the acting seat's land and the owner map ----------------------------------------------------------------


# ---- the actors and the agent economy ----------------------------------------------------------------------------------------





@bridge_view("legacy_labour")
def legacy_labour(sim):
    """The workforce module's labour implementation, for engine code and mods that still call its members."""
    return sim.assembly.modules["workforce"].labour
