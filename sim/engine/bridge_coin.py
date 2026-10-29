"""Bridge entries the coin module uses until the modules that own these facts move.

Each view answers through `Sim` as the old mixin methods did; when its owner moves it publishes the same name and the
entry is deleted."""
from sim.demography.api import TakeFromGranary
from sim.ledger.api import STORE_ACTOR, STORE_GRANARY, STORE_STOCK, DrawDownStock, TakeGoods

from .bridge import bridge_command


# ---- the home country (the actors' cast, behind the coin module's reads) ----

# ---- commands ----

@bridge_command(TakeGoods)
def take_goods(sim, command):
    """Thieves take tonnes of a good out of a holder's store, never below zero, into an edge's goods."""
    if command.store == STORE_ACTOR:
        stores = sim.view("cast")().actors[command.actor].record.stores
        stores[command.good] = max(0.0, stores[command.good] - command.tonnes)
    elif command.store == STORE_STOCK:
        sim.send(DrawDownStock(command.good, command.tonnes))
    elif command.store == STORE_GRANARY:
        sim.send(TakeFromGranary(command.tonnes * 1000.0))
    sim.view("legacy_edge_account")[command.edge].receive_goods(command.good, command.tonnes)
