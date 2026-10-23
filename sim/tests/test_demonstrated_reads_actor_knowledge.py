"""SCENARIO (wiring, one game): Complaint 491: `demonstrated()` reads every actor's known nodes as well as the seats' builds, so imitation can
copy a node from any actor that holds it."""
from .harness import *  # noqa: F401,F403

from sim.agents import imitation
from sim.agents.api import ActorRecord, Firm, Player
from sim.engine.agents_port import SimWorld

game = unopened_sim()
baseline = SimWorld(game).baseline_knowledge()
node_id = next(node for node in sorted(game.nodes) if node not in baseline and not game.nodes[node].get("win_condition")
			   and all(pre in baseline for pre in game.nodes[node]["pre"]))

government = next(actor for actor in game.actors.actors.values() if actor.kind == "government")
check("scenario: a node nobody holds is not demonstrated", node_id not in SimWorld(game).demonstrated())
government.knowledge.add(node_id)
world = SimWorld(game)
check("scenario: a node a state holds is demonstrated", node_id in world.demonstrated(), node_id)
check("...and is not a seat's invention", node_id not in world.founder_inventions())
check("...and can be seen from the holder's own place", world.exposure(node_id, government.location()) > 0.0,
	  world.exposure(node_id, government.location()))

learner = Firm("firm:test", ActorRecord(kind="firm", money=10 ** 7, founded_year=world.year, location=government.location()))
check("scenario: a node a state holds is a candidate for imitation", node_id in Player("player:test", ActorRecord(kind="player")).imitation_candidates(world))
learner.record.target = node_id
check("scenario: a firm aiming at it finds it demonstrated", learner.imitation_candidates(world) == [node_id])
check("scenario: the chain to copy it is the node itself", imitation.missing_chain(node_id, world, learner) == [node_id])

government.knowledge.discard(node_id)
check("scenario: a node no actor holds any more is no longer demonstrated", node_id not in SimWorld(game).demonstrated())
