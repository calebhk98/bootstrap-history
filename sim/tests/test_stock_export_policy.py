"""A partner's refusal to sell is its state's decision (Complaints/366): the export policy of the country's
government actor, started from the monopolies its country's data gives it, with no flag read by the trade.
Also the pure rules of held stock: growth held to what its feed carries, and a smuggler's chance of being caught."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, Decision, Option, ValuePolicy
from sim.agents import government_foreign  # noqa: F401  (registers the foreign government)
from sim.agents.cast import cast_from_civilisations, seed_cast
from sim.agents.policy import ExportPolicy, exports_allowed
from sim.engine.civ_basket_check import _sells_abroad
from sim.world import stock_dynamics

# ---- growth held to feed ------------------------------------------------------------------
check("with no room given a herd grows by its rate",
      abs(stock_dynamics.next_units(100.0, 0.2, 0.05, 10.0) - 115.0) < 1e-9)
check("room smaller than the growth holds the growth to the room",
      abs(stock_dynamics.next_units(100.0, 0.2, 0.05, 10.0, 8.0) - 103.0) < 1e-9)
check("no room means no growth, and the loss still falls",
      abs(stock_dynamics.next_units(100.0, 0.2, 0.05, 10.0, 0.0) - 95.0) < 1e-9)
check("negative room is no room", abs(stock_dynamics.next_units(100.0, 0.2, 0.05, 10.0, -5.0) - 95.0) < 1e-9)
check("room larger than the growth changes nothing",
      abs(stock_dynamics.next_units(100.0, 0.2, 0.05, 10.0, 1e9) - 115.0) < 1e-9)
check("feed room is what the capacity has beside the held weight, never negative",
      stock_dynamics.feed_room(500.0, 200.0) == 300.0 and stock_dynamics.feed_room(100.0, 200.0) == 0.0)

# ---- a smuggler's chance of being caught --------------------------------------------------
check("a state that reaches nothing catches nothing", stock_dynamics.catch_chance(0.0, 1.0) == 0.0)
check("a taking nobody sees is not caught", stock_dynamics.catch_chance(0.9, 0.0) == 0.0)
check("the chance is the state's reach times the visibility",
      abs(stock_dynamics.catch_chance(0.8, 0.5) - 0.4) < 1e-12)
check("the chance is a probability", 0.0 <= stock_dynamics.catch_chance(5.0, 5.0) <= 1.0)
check("a draw inside the chance is caught and one outside is not",
      stock_dynamics.is_caught(0.3, 0.4) and not stock_dynamics.is_caught(0.4, 0.4))

# ---- the export policy decides -------------------------------------------------------------
def actor_with(monopolies, policy=None):
    return SimpleNamespace(record=SimpleNamespace(state_monopolies=set(monopolies)), decision_policy=policy)


check("a state with no monopoly sells what it is asked to",
      exports_allowed(actor_with([]), ["silk", "eggs"]) == ["eggs", "silk"])
check("a state holds its monopoly back and sells the rest",
      exports_allowed(actor_with(["eggs"]), ["silk", "eggs"]) == ["silk"])
check("a state's own policy answers when it has one",
      exports_allowed(actor_with(["eggs"], ExportPolicy()), ["eggs"]) == [])
other = ExportPolicy().choose(actor_with(["eggs"]), Decision("copy", [Option("eggs", 2.0, 1.0)], 10.0))
plain = ValuePolicy().choose(actor_with(["eggs"]), Decision("copy", [Option("eggs", 2.0, 1.0)], 10.0))
check("any decision but an export is taken as the value policy takes it",
      [option.subject for option in other] == [option.subject for option in plain] == ["eggs"])
check("the data check for a civilisation asks the same policy",
      not _sells_abroad({"state_monopolies": ["eggs"]}, "eggs") and _sells_abroad({"state_monopolies": ["eggs"]}, "silk")
      and _sells_abroad({}, "eggs"))

# ---- the monopoly is the actor's own record, started from its country's data ---------------
HOME = {"id": "alpha", "name": "Alpha", "home_tiles": ["algeria_01"]}
FAR = {"id": "far", "name": "Far", "home_tiles": ["algeria_02"], "state_monopolies": ["eggs"]}
home_country, entries, profiles = cast_from_civilisations(HOME, [FAR])
registry = ActorRegistry(ActorsState())
seed_cast(registry, home_country, entries, profiles)
state = registry.actors["government:far"]
check("a country's state starts with the monopolies its data lists", state.record.state_monopolies == {"eggs"},
      state.record.state_monopolies)
check("a state without any starts with none", registry.actors["government:alpha"].record.state_monopolies == set())
check("the state decides through its own export policy", state.exports_allowed(["eggs", "silk"]) == ["silk"])
state.record.state_monopolies.discard("eggs")
check("the decision follows the record, not the data it started from", state.exports_allowed(["eggs"]) == ["eggs"])

# ---- shutting markets to a party -------------------------------------------------------------
check("a state's markets are open to a party it has not shut out", state.markets_closed_until("thief", 100) == 0)
state.close_markets_to("thief", 110)
check("a shut market names the year it reopens", state.markets_closed_until("thief", 100) == 110)
check("...and is open to another party", state.markets_closed_until("honest", 100) == 0)
check("...and reopens in that year", state.markets_closed_until("thief", 110) == 0)
state.close_markets_to("thief", 105)
check("a later closure does not shorten an earlier one", state.markets_closed_until("thief", 100) == 110)
check("a record that never had markets shut is a fresh record", ActorRecord().closed_markets == {} and ActorRecord().stock_taken == {})
