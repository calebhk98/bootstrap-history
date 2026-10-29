"""Bridge entries the materials module reads, and the market commands it sends, until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code
did, and is never cached."""
from sim.assembly.api import QUOTE

from . import view_share
from .bridge import bridge_view


# ---- the catalogue of commodities, the price epoch and the producers ----

# ---- projects' costs and what the seat can pay ----

@bridge_view("shared_bill", kind=QUOTE)
def shared_bill(sim, node_id, compute):
    """A project's material bill, reused inside a view's scope while the world and the node's stock hold."""
    return view_share.of(sim)._shared_bill(node_id, compute)
