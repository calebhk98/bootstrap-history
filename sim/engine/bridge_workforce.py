"""Bridge entries the workforce module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
labour adapter did, and is never cached. The `legacy_*` views are raw state the module still reads or writes in place;
they go when that state moves."""
from sim.assembly.api import QUOTE

from . import view_share

from .bridge import bridge_view


@bridge_view("provider_game")
def provider_game(sim):
    """The game itself, for the functions a mod provides to the town and director-overhead points of the workforce module and to
    the wealth-claim point of the polity module: their contract hands them the game to read (a mod's stores, a mod's holdings),
    and they never write it. A debt of the mod interface."""
    return sim


# ---- the founder, the acting seat's land and the owner map ----------------------------------------------------------------


# ---- the actors and the agent economy ----------------------------------------------------------------------------------------

@bridge_view("shared_answer", kind=QUOTE)
def shared_answer(sim, key, inputs, compute, standalone=False):
    """`compute()` reused while the engine's world stamp and `inputs` hold."""
    return view_share.of(sim)._shared_answer(key, inputs, compute, standalone)




@bridge_view("legacy_labour")
def legacy_labour(sim):
    """The workforce module's labour implementation, for engine code and mods that still call its members."""
    return sim.assembly.modules["workforce"].labour
