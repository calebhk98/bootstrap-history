"""SCENARIO (Complaint 640): Complaint 491: the founder's start is a caller of `research.begin`, the path every actor uses, and the same
node costs the founder and an actor the same bill."""

from .harness import *  # noqa: F401,F403

from sim.agents import research
from sim.agents.api import ActorRecord, Player
from sim.engine.agents_port import SimWorld
from sim.engine.seat_researcher import SeatResearcher

game = sim(civ="rome_100ad", capital=500000)
node_id = next(node for node in sorted(game.nodes) if not game.nodes[node]["sch"] and not game.nodes[node]["art"]
			   and game.nodes[node]["ph"] > 0 and game.can_start(node))

begun = []
original = research.begin


def spy(actor, node, world):
	begun.append((type(actor).__name__, node))
	return original(actor, node, world)


research.begin = spy
try:
	started, refusal = game.start_project(node_id)
finally:
	research.begin = original
check("a founder's start goes through the shared research path with the seat as researcher",
	  started and begun == [("SeatResearcher", node_id)] and node_id in game.state.projects.active, (started, refusal, begun))

# the shared gate refuses with a cause the reply can carry
poor = sim(civ="rome_100ad", capital=500000)
needing = next(node for node in sorted(poor.nodes) if poor.nodes[node]["sch"] > poor.labour.scholar_hands_available()
			   and not [pre for pre in poor.nodes[node]["pre"] if pre not in poor.state.projects.done])
try:
	research.begin(SeatResearcher(poor), needing, SimWorld(poor))
	cause = None
except Exception as reason:
	cause = reason.args[0].cause
check("the shared gate refuses a seat that lacks the scholars, with the cause", cause == "scholar_staff", cause)

# the same node costs an actor with the same staff the founder's bill
world = SimWorld(game)
player = Player("player:9", ActorRecord(kind="player", money=10 ** 9, founded_year=world.year))
player.workforce.update({trade: 1.0 for trade in game.nodes[node_id]["lab"]})
fresh = sim(civ="rome_100ad", capital=500000)
price = SeatResearcher(fresh).research_price({}, node_id, SimWorld(fresh))
plan = research.plan(player, node_id, world)
check("an actor with the staff pays what the founder's bill is for the same node",
	  abs(plan["total"] - price) < 1e-6 * max(1.0, price), (plan["total"], price))
