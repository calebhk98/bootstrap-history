"""Bridge entries the prices module reads until the owners behind them move into modules.

Each view carries the name its owner will publish, asks the engine exactly as the old code did, and is never cached."""
from sim.assembly.api import KEYED

from .bridge import bridge_view


@bridge_view("concern_baskets_now", kind=KEYED)
def concern_baskets_now(sim, node_id):
    """What a concern makes and buys in a year with the techniques held now; None for a node whose revenue is not derived
    from output."""
    return sim.concern_baskets_now(node_id)


@bridge_view("venture_ramp", kind=KEYED)
def venture_ramp(sim, node_id):
    """How much of its full takings a concern is making, 0..1."""
    return sim.venture_ramp(node_id)
