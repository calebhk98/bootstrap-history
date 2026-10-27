"""Bridge entries the freight module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
code did, and is never cached."""
from sim.agents.api import GOVERNMENT_PREFIX, ledger
from sim.assembly.api import KEYED, QUOTE
from sim.land.api import action_results
from sim.ledger.api import PayActor

from .bridge import bridge_command, bridge_view


# ---- knowledge ----

@bridge_view("techniques_with_results", kind=QUOTE)
def techniques_with_results(sim, techniques):
    """`techniques` with the routes, partners and knowledge their nodes return."""
    return action_results.expand(sim.nodes, techniques)



# ---- polity and the ledger ----

@bridge_view("holder_treasury", kind=KEYED)
def holder_treasury(sim, holder):
    """The id of the account a country's or seat's dues are paid into: the seat itself (paid as its party), else the
    country's government."""
    if holder in sim.state.seats:
        return holder
    government = sim.actors.government_of(holder)
    return government.actor_id if government is not None else GOVERNMENT_PREFIX + str(holder)


@bridge_command(PayActor)
def pay_actor(sim, command):
    """The payer pays the payee through the ledger's transfer; a government not yet in the cast is opened."""
    if command.payee in sim.state.seats:
        payee = sim.seat_party(command.payee)
    else:
        payee = sim.actors.get(command.payee) or sim.actors.ensure_government(command.payee[len(GOVERNMENT_PREFIX):])
    ledger.transfer(sim.actors.get(command.payer), payee, command.amount, command.purpose)
