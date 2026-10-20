"""Complaint 622: in a running game a levy on a non-grain good reads what the home producers made of it last
year from the agent economy, in tonnes, and takes the rate of it into the state's stores."""
from .harness import *  # noqa: F401,F403
import random

from sim.agents import revenue
from sim.economy import api as economy_api
from sim.engine.agents_port import SimWorld

GOOD = "cloth_kg"
RATE = 0.1

game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ("rome_100ad"))
game.goal, game.done_year = GOAL, {}
game.step()
game.step()

agent = game.economy.agent
world = SimWorld(game)
held = set(world.held_tiles())
units = sum(row.get(GOOD, 0.0) for tile, row in economy_api.output_by_tile(agent.economy()).items() if tile in held)
tonnes = world.output_tonnes(GOOD)
check("the economy records what the home producers made of a good, by tile", units > 0.0, units)
check("the world reports it in tonnes (a thousand units to the tonne)", abs(tonnes - units / 1000.0) < 1e-9 * max(1.0, units), (tonnes, units))
check("limited to a tile it reports only that tile's output",
      0.0 <= world.output_tonnes(GOOD, frozenset(sorted(held)[:1])) <= tonnes)

game.civ["state_revenue"] = [{"form": "cloth_levy", "basis": "harvest", "rate": RATE, "paid_in": GOOD}]
levy = revenue.assess(SimWorld(game))[0]
check("a levy on cloth takes its rate of the cloth made, in kind", levy.in_kind and abs(levy.tonnes - RATE * tonnes) < 1e-9 * max(1.0, tonnes), (levy, tonnes))
check("the cloth taken is valued at the price the economy quotes",
      abs(levy.money - levy.tonnes * SimWorld(game).material_price(GOOD)) < 1e-6 * max(1.0, levy.money), levy)

treasury = game.state_treasury()
treasury.record.stores.pop(GOOD, None)
treasury.receive_revenue(SimWorld(game))
check("the cloth levied is in the state's stores", abs(treasury.record.stores.get(GOOD, 0.0) - levy.tonnes) < 1e-9 * max(1.0, levy.tonnes), treasury.record.stores)
