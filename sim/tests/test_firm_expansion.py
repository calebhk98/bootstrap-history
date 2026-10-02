"""Complaint 331: a firm in a growing market grows before another firm is needed. An incumbent whose
added capacity earns more than the capital costs expands, an entrant expects what is left after that,
and a market that stops growing stops gaining capacity and firms."""
from .harness import *  # noqa: F401,F403

from sim.engine.actors import SimWorld

import copy
import json
import os
import random
import tempfile

from sim.engine.protocol import load_state, save_state
from sim.engine.state import ActorRecord  # noqa: F401

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if node["rev"] > 0 and not node["pre"] and node["cap"] >= 0)


def make_node(node_id, category, revenue, upkeep, hours):
	node = copy.deepcopy(NODES[_TEMPLATE_ID])
	node.update(id=node_id, name=node_id, traits=["commerce"], pre=[], lab={"labourer": hours},
	            mat={}, rev=revenue, up=upkeep, yrs=1.0, risk=0.0, ph=0.0,
	            dev_years=None, dev_people=None, cat=category)
	node.pop("gains", None)
	return node


def actor_sim(extra_nodes):
	nodes = copy.deepcopy(NODES)
	for node in extra_nodes:
		nodes[node["id"]] = node
	game = S.Sim(nodes, list(ORDER), random.Random(1), events=False, manual=True,
	             civ=S.load_civ("rome_100ad"), cfg={"agent_economy": False})
	game.goal, game.done_year = GOAL, {}
	return game


def founder_runs(game, node_id, opened_ago):
	year = game.state.scenario.year
	projects = game.state.projects
	projects.done.add(node_id)
	projects.done_year[node_id] = year - opened_ago
	projects.operating.add(node_id)
	projects.opened_year[node_id] = year - opened_ago
	game._done_changed()


def next_year(game):
	game.state.scenario.year += 1
	game.advance_actors(game.state.scenario.year)


CATEGORY = sorted(S.Sim.GOODS_CATEGORIES)[0]
NODE = make_node("zz_grow", CATEGORY, revenue=2.0e5, upkeep=5000.0, hours=50.0)


def settled(rate=0.12, years=40):
	game = actor_sim([NODE])
	game.market_rate = lambda: rate
	founder_runs(game, "zz_grow", opened_ago=10)
	for _ in range(years):
		next_year(game)
	return game


def total_capacity(game):
	return sum(firm.record.capacity.get("zz_grow", 1.0) for firm in game.actors.active_firms())


def market_grows(sim_game, times):
	"""Demand for the good rises `times`-fold while the same hands tend it: a bigger market, not a
	bigger economy, so what a concern must carry stays put (the economy index scales costs with takings)."""
	hands = sim_game.venture_hands("zz_grow")
	sim_game.nodes["zz_grow"]["rev"] *= times
	sim_game.venture_hands = lambda node_id: hands


game = settled()
firms_before = len(game.actors.active_firms())
capacity_before = total_capacity(game)
check("some firm entered before the market grew", firms_before > 0, firms_before)

# the market grows tenfold: every concern's takings rise with it
market_grows(game, 10.0)
next_year(game)
grown = [firm for firm in game.actors.active_firms() if firm.record.capacity.get("zz_grow", 1.0) > 1.0]
check("an incumbent in a growing market with a margin above the cost of capital adds capacity", len(grown) > 0,
      (len(game.actors.active_firms()), total_capacity(game)))
check("the expansion was paid for: outlays name it", all(firm.record.outlays.get("expansion", 0.0) > 0.0 for firm in grown))
for _ in range(25):
	next_year(game)
firms_after = len(game.actors.active_firms())
capacity_after = total_capacity(game)
check("the market's growth is served by capacity at least as much as by firm count",
      capacity_after / capacity_before >= firms_after / firms_before,
      (capacity_before, capacity_after, firms_before, firms_after))
check("a firm ends larger than it was founded",
      max(firm.record.capacity.get("zz_grow", 1.0) for firm in game.actors.active_firms()) > 1.5)

# an entrant expects what incumbents' expansion leaves
fresh = settled(years=40)
before = SimWorld(fresh).entry_gross("zz_grow", fresh.actors.rivals_of("zz_grow", ""), 1)
fresh.actors.active_firms()[0].record.capacity["zz_grow"] = 6.0
fresh.actors.note_capacity_change()
after = SimWorld(fresh).entry_gross("zz_grow", fresh.actors.rivals_of("zz_grow", ""), 1)
check("an entrant expects less once an incumbent has expanded", after < before, (before, after))

# no growth, no further expansion or entry
steady = settled(years=80)
snapshot = (len(steady.actors.active_firms()), round(total_capacity(steady), 6))
for _ in range(10):
	next_year(steady)
check("a market that stops growing stops gaining firms and capacity",
      (len(steady.actors.active_firms()), round(total_capacity(steady), 6)) == snapshot,
      (snapshot, len(steady.actors.active_firms()), total_capacity(steady)))

# capital dearer than any margin: no expansion
dear = actor_sim([NODE])
dear.market_rate = lambda: 1.0e5
founder_runs(dear, "zz_grow", opened_ago=10)
for _ in range(10):
	next_year(dear)
market_grows(dear, 10.0)
for _ in range(5):
	next_year(dear)
check("a cost of capital above the added margin stops expansion",
      all(firm.record.capacity.get("zz_grow", 1.0) == 1.0 for firm in dear.actors.active_firms()))

# a firm that loses money does not expand
loser_world = settled(years=5)
sizes = {firm.actor_id: dict(firm.record.capacity) for firm in loser_world.actors.active_firms()}
for firm in loser_world.actors.active_firms():
	firm.record.last_margin = -1.0
	firm.expand(SimWorld(loser_world))
check("a firm with no margin does not expand",
      all(firm.record.capacity == sizes[firm.actor_id] for firm in loser_world.actors.active_firms()))

# capacity survives a save and load
with tempfile.TemporaryDirectory() as folder:
	path = os.path.join(folder, "save.json")
	save_state(game, path)
	revived = actor_sim([NODE])
	load_state(revived, path)
check("capacity round-trips through save and load",
      revived.state.actors.records == game.state.actors.records
      and any(record.capacity for record in revived.state.actors.records.values()))
