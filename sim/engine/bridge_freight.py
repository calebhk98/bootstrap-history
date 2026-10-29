"""Bridge entries the freight module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
code did, and is never cached."""
from sim.agents.api import GOVERNMENT_PREFIX
from sim.assembly.api import KEYED, QUOTE

from .bridge import bridge_view




# ---- polity ----

@bridge_view("holder_treasury", kind=KEYED)
def holder_treasury(sim, holder):
    """The id of the account a country's or seat's dues are paid into: the seat itself (paid as its party), else the
    country's government."""
    if holder in sim.state.seats:
        return holder
    government = sim.view("cast")().government_of(holder)
    return government.actor_id if government is not None else GOVERNMENT_PREFIX + str(holder)
