"""Bridge entries the living-stock and defence-stores modules use until the modules that own these facts move.

Each view answers through `Sim` as the old mixin methods did; when its owner moves it publishes the same name and the
entry is deleted. The `partner_*` views carry the foreign-trade and polity arithmetic that used to sit in the
living-stock mixins (a partner's landed price, the carriage of a smuggled load, a state's chance to catch it)."""
from sim.agents.api import GOVERNMENT_PREFIX
from sim.assembly.api import KEYED, QUOTE
from sim.world import stock_dynamics

from .bridge import bridge_view
from sim.coin.api import visibility_factor


# ---- facts of the world and the game's data ----


# ---- partners ----

@bridge_view("partner_catch_chance", kind=QUOTE)
def partner_catch_chance(sim, civilization_id, share_of_holding):
    """Chance the partner's state finds out a taking of this share of what it holds: its reach (what its paid
    officials collect of what is due over its roads) against how visible the bite is."""
    registry = sim.view("seeded_actor_registry")()
    reach = float(registry.world_for(registry.get(GOVERNMENT_PREFIX + civilization_id), sim.view("actor_world")()).state_reach())
    return stock_dynamics.catch_chance(reach, visibility_factor(share_of_holding))


# ---- what is built and running ----

