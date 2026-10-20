"""Complaint 141: the cost of a simulated year must not grow with the number of built nodes and firms through repeated
whole-set scans. Counted work, not seconds. Each rule is called on the object that owns it: a firm in a registry over a
fixture world, and the incumbent price cache on a stub game."""
QUICK_TOPIC = True

import types

from .harness import *  # noqa: F401,F403

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, Business, Firm
from sim.engine.incumbent_prices import IncumbentPricesMixin

from .agents_fake_world import FakeWorld, make_node

FIRM_COUNT = 150
INVENTION_COUNT = 80
SHARED = ["shared_a", "shared_b", "shared_c"]


def crowded_registry():
    """A registry of many firms aiming at three shared concerns, in a world where many inventions are on show."""
    world = FakeWorld(year=50)
    for name in SHARED + ["invention_%d" % number for number in range(INVENTION_COUNT)]:
        world.nodes[name] = make_node(name, hours=100.0, revenue=10.0, upkeep=1.0)
        world.demonstrated_nodes.add(name)
    registry = ActorRegistry(ActorsState(home_country="home"))
    registry.world = world
    for firm_number in range(FIRM_COUNT):
        target = SHARED[firm_number % 3]
        record = ActorRecord(kind="firm", money=1e6, target=target, business=Business.running([target], opened_year=0))
        registry.add("firm:%d" % (firm_number + 1), record)
    return registry, world


# --- a firm weighs only the concern it is aiming at -------------------------
registry, world = crowded_registry()
worth_calls = [0]
real_worth = Firm.imitation_worth


def counting_worth(self, node_id, world_view):
    worth_calls[0] += 1
    return real_worth(self, node_id, world_view)


Firm.imitation_worth = counting_worth
try:
    for firm in registry.of_kind("firm"):
        firm.imitation_options(world)
finally:
    Firm.imitation_worth = real_worth
check("a firm's candidates are its own target alone, not every invention in the world",
      all(firm.imitation_candidates(world) in ([firm.record.target], []) for firm in registry.of_kind("firm"))
      and len(world.demonstrated()) > 50, len(world.demonstrated()))
check("a firm prices at most its own target, not every invention in the world",
      worth_calls[0] <= FIRM_COUNT, (worth_calls[0], FIRM_COUNT * INVENTION_COUNT))

# --- asking who shares a concern's market does not visit every firm ---------
registry, world = crowded_registry()
concern_reads = [0]
real_concerns = Firm.concerns


def counting_concerns(self):
    concern_reads[0] += 1
    return real_concerns.fget(self)


Firm.concerns = property(counting_concerns)
try:
    answers = [registry.rivals_of(SHARED[0], "firm:1") for _ in range(50)]
finally:
    Firm.concerns = real_concerns
check("rivals_of still counts the other operators of the concern",
      answers[0] == FIRM_COUNT // 3 - 1, answers[0])
check("50 rivals_of questions do not each visit every firm", concern_reads[0] < 50 * FIRM_COUNT // 4, concern_reads[0])

# --- the calculator's price table is not rebuilt from the done set per lookup
table_builds = [0]
hours = {"iron_kg": 2.0, "wheat_kg": 0.5}


def counting_tables():
    table_builds[0] += 1
    return hours, {}


per_hour = [10.0]
stub = types.SimpleNamespace(_price_tables=counting_tables,
                             labour=types.SimpleNamespace(money_per_labour_hour=lambda: per_hour[0]))
first = IncumbentPricesMixin._material_prices(stub)
for _ in range(3000):
    again = IncumbentPricesMixin._material_prices(stub)
check("repeated price lookups return the one cached table", again is first and first == {"iron_kg": 20.0, "wheat_kg": 5.0}, first)
per_hour[0] = 20.0
check("the cached table is rebuilt when the money per hour moves",
      IncumbentPricesMixin._material_prices(stub) == {"iron_kg": 40.0, "wheat_kg": 10.0}, "stale prices")
hours = {"iron_kg": 3.0}
stub._price_tables = lambda: (hours, {})
check("...and when the solved table is replaced", IncumbentPricesMixin._material_prices(stub) == {"iron_kg": 60.0}, "stale prices")
