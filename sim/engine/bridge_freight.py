"""Bridge entries the freight module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
code did, and is never cached."""
from sim.assembly.api import QUOTE
from sim.land.api import action_results

from .bridge import bridge_view


# ---- knowledge ----

@bridge_view("techniques_with_results", kind=QUOTE)
def techniques_with_results(sim, techniques):
    """`techniques` with the routes, partners and knowledge their nodes return."""
    return action_results.expand(sim.nodes, techniques)



# ---- polity ----

