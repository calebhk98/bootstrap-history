"""Bridge entries the disease module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
disease adapter did, and is never cached. The `legacy_*` view is raw state the module still needs; it goes when that
state moves."""
from sim.assembly.api import KEYED

from .bridge import bridge_view


# ---- land and public works -----------------------------------------------------------------------------------------

@bridge_view("home_tiles_held")
def home_tiles_held(sim):
    """The tiles the home country owns, sorted."""
    return sim.home_tiles_held()


@bridge_view("coverage_share", kind=KEYED)
def coverage_share(sim, node_id):
    """The share of the people who can use the work that it serves while it is open, 0 to 1."""
    return sim.coverage_share(node_id)
