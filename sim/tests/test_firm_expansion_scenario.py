"""Scenario: Complaint 331 in a game. An entrant expects less once an incumbent has expanded. The rules (the return against
the cost of capital, the margin gate, the ceiling, rivals counted by capacity) are in test_firm_expansion.
The long-run split of a growing market between capacity and firm count is not tested: it was phase luck over 40 years."""
from .harness import *  # noqa: F401,F403

from sim.engine.agents_port import SimWorld

import copy
import random


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


def settled(rate=0.12, years=3):
	game = actor_sim([NODE])
	game.market_rate = lambda: rate
	founder_runs(game, "zz_grow", opened_ago=10)
	for _ in range(years):
		next_year(game)
	return game


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
