"""Scenario: Complaint 331 in a game. An entrant expects less once an incumbent has expanded, a growing market is served by
capacity at least as much as by firm count, and capacity survives a save and load. The rules (the return against the cost
of capital, the margin gate, the ceiling, rivals counted by capacity) are in test_firm_expansion."""
from .harness import *  # noqa: F401,F403

from sim.engine.agents_port import SimWorld

import copy
import json
import os
import random
import tempfile

from sim.ui.protocol import load_state, save_state
from sim.engine.state import ActorRecord  # noqa: F401

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if not node["pre"] and node["cap"] >= 0)


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
	game = build_unopened(lambda: S.Sim(nodes, list(ORDER), random.Random(1), events=False, manual=True,
	             civ=S.load_civ("rome_100ad")))
	game.goal, game.done_year = GOAL, {}
	return ready_for_entry(game)


def founder_runs(game, node_id, opened_ago):
	year = game.state.scenario.year
	projects = game.state.projects
	projects.done.add(node_id)
	projects.done_year[node_id] = year - opened_ago
	projects.operating.add(node_id)
	projects.business.set_opened_year(node_id, year - opened_ago)
	game._done_changed()


def next_year(game):
	game.state.scenario.year += 1
	game.advance_actors(game.state.scenario.year)


CATEGORY = sorted(S.Sim.GOODS_CATEGORIES)[0]
NODE = make_node("zz_grow", CATEGORY, revenue=2.0e5, upkeep=5000.0, hours=50.0)


def settled(rate=0.12, years=24):     # since 679 the count and capacity come to rest more slowly: at 12 years capacity is still rising
	game = actor_sim([NODE])
	game.market_rate = lambda: rate
	founder_runs(game, "zz_grow", opened_ago=10)
	for _ in range(years):
		next_year(game)
	return game


def total_capacity(game):
	return sum(firm.capacity_of("zz_grow") for firm in game.actors.active_firms())


def market_grows(sim_game, times):
	"""Demand for the good rises `times`-fold while the same hands tend it: a bigger market, not a
	bigger economy, so what a concern must carry stays put (the economy index scales costs with takings)."""
	hands = sim_game.venture_hands("zz_grow")
	staff = sim_game.concern_staff_by_trade("zz_grow")       # the site rent and manager hours an added step carries read the crew
	sim_game.nodes["zz_grow"]["rev"] *= times
	sim_game.venture_hands = lambda node_id: hands
	sim_game.concern_staff_by_trade = lambda node_id: staff


game = settled()

# an entrant expects what incumbents' expansion leaves
entry_before = SimWorld(game).entry_gross("zz_grow", game.actors.rivals_of("zz_grow", ""), 1)
incumbent = game.actors.active_firms()[0]
founded_capacity = incumbent.capacity_of("zz_grow")
incumbent.business.set_size("zz_grow", 6.0)
game.actors.note_capacity_change(incumbent.actor_id)
entry_after = SimWorld(game).entry_gross("zz_grow", game.actors.rivals_of("zz_grow", ""), 1)
check("an entrant expects less once an incumbent has expanded", entry_after < entry_before, (entry_before, entry_after))
incumbent.business.set_size("zz_grow", founded_capacity)
game.actors.note_capacity_change(incumbent.actor_id)

# no growth, no further expansion or entry
steady_snapshot = (len(game.actors.active_firms()), round(total_capacity(game), 6))
for _ in range(5):
	next_year(game)
check("a market that stops growing stops gaining firms and capacity",
      (len(game.actors.active_firms()), round(total_capacity(game), 6)) == steady_snapshot,
      (steady_snapshot, len(game.actors.active_firms()), total_capacity(game)))

firms_before = len(game.actors.active_firms())
capacity_before = total_capacity(game)
check("some firm entered before the market grew", firms_before > 0, firms_before)

# the market grows tenfold: every concern's takings rise with it
market_grows(game, 10.0)
next_year(game)
grown = [firm for firm in game.actors.active_firms() if firm.capacity_of("zz_grow") > 1.0]
check("an incumbent in a growing market with a margin above the cost of capital adds capacity", len(grown) > 0,
      (len(game.actors.active_firms()), total_capacity(game)))
check("the expansion was paid for: outlays name it", all(firm.record.outlays.get("expansion", 0.0) > 0.0 for firm in grown))
for _ in range(12):
	next_year(game)
firms_after = len(game.actors.active_firms())
capacity_after = total_capacity(game)
check("the market's growth is served by capacity at least as much as by firm count",
      capacity_after / capacity_before >= firms_after / firms_before,
      (capacity_before, capacity_after, firms_before, firms_after))
check("a firm ends larger than it was founded",
      max(firm.capacity_of("zz_grow") for firm in game.actors.active_firms()) > 1.5,
      sorted(firm.capacity_of("zz_grow") for firm in game.actors.active_firms()))

# capacity survives a save and load
with tempfile.TemporaryDirectory() as folder:
	path = os.path.join(folder, "save.json")
	save_state(game, path)
	revived = actor_sim([NODE])
	load_state(revived, path)
check("capacity round-trips through save and load",
      revived.state.actors.records == game.state.actors.records
      and any(plant.size != 1.0 for record in revived.state.actors.records.values() for plant in record.business.plants))
