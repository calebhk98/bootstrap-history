"""Complaint 141: the cost of a simulated year must not grow with the number of
built nodes and firms through repeated whole-set scans. Counted work, not seconds."""
from .harness import *  # noqa: F401,F403
import sim.engine.data as engine_data
from sim.agents.api import Firm
from sim.engine.agents_port import SimWorld
from sim.engine.state import ActorRecord

FIRM_COUNT = 150
INVENTION_COUNT = 80


def _crowded_sim():
    game = sim(capital=1e9)
    for node_id in [node for node in ORDER if node not in game.done][:INVENTION_COUNT]:
        game.state.projects.done.add(node_id)
    game._done_changed()
    shared = sorted(game.state.projects.done)[:3]
    for firm_number in range(FIRM_COUNT):
        record = ActorRecord(kind="firm", money=1e6, target=shared[firm_number % 3])
        record.concerns = {shared[firm_number % 3]}
        game.actors.add("firm:%d" % (firm_number + 1), record)
    return game, shared


# --- a firm weighs only the concern it is aiming at -------------------------
game, shared = _crowded_sim()
world = SimWorld(game)
worth_calls = [0]
real_worth = Firm.imitation_worth


def counting_worth(self, node_id, world_view):
    worth_calls[0] += 1
    return real_worth(self, node_id, world_view)


Firm.imitation_worth = counting_worth
try:
    for firm in game.actors.of_kind("firm"):
        firm.imitation_options(world)
finally:
    Firm.imitation_worth = real_worth
check("set-up: many inventions and many firms", len(world.founder_inventions()) >= 50 and FIRM_COUNT >= 100)
check("a firm prices its own target, not every invention in the world",
      worth_calls[0] <= FIRM_COUNT * 3, (worth_calls[0], FIRM_COUNT * INVENTION_COUNT))

# --- asking who shares a concern's market does not visit every firm ---------
game, shared = _crowded_sim()
registry = game.actors
registry.world = SimWorld(game)
concern_reads = [0]
real_concerns = Firm.concerns


def counting_concerns(self):
    concern_reads[0] += 1
    return real_concerns.fget(self)


Firm.concerns = property(counting_concerns)
try:
    answers = [registry.rivals_of(shared[0], "firm:1") for _ in range(50)]
finally:
    Firm.concerns = real_concerns
check("rivals_of still counts the other operators", answers[0] == FIRM_COUNT // 3 - 1 or answers[0] == FIRM_COUNT // 3, answers[0])
check("50 rivals_of questions do not each visit every firm",
      concern_reads[0] < 50 * FIRM_COUNT // 4, concern_reads[0])

# --- the calculator's price table is not rebuilt from the done set per lookup
price_sim = sim(capital=1e9)
for node_id in [node for node in ORDER if node not in price_sim.done][:400]:
    price_sim.state.projects.done.add(node_id)
price_sim._done_changed()
price_sim._material_prices()
lookups = 3000

table_builds = [0]
real_table = engine_data.calculated_goods_table


def counting_table(*args, **kwargs):
    table_builds[0] += 1
    return real_table(*args, **kwargs)


engine_data.calculated_goods_table = counting_table
try:
    for _ in range(lookups):
        price_sim._material_prices()
finally:
    engine_data.calculated_goods_table = real_table
check("repeated price-table lookups rebuild the table", table_builds[0] == 0, table_builds[0])
