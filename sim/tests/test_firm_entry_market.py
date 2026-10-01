"""Complaint 535, part 1: entry is bounded by the market. An entrant expects what it would earn after
its own output and that of the entrants already waiting reaches the market, and enters only while
that covers the capital it ties up at the market's rate; nothing caps the number of firms."""
from .harness import *  # noqa: F401,F403

from sim.engine.actors import SimWorld

import copy
import random

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
	             civ=S.load_civ("rome_100ad"))
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
NODE = make_node("zz_entry", CATEGORY, revenue=2.0e5, upkeep=5000.0, hours=50.0)


def run_entry(years, rate_scale=1.0):
	game = actor_sim([NODE])
	game.market_rate = lambda: 40.0 * 0.12 if rate_scale > 1.0 else 0.12
	founder_runs(game, "zz_entry", opened_ago=10)
	counts = []
	for _ in range(years):
		next_year(game)
		counts.append(len(game.actors.active_firms()))
	return game, counts


game, counts = run_entry(40)
world = SimWorld(game)
check("more sellers in a market leave each an entrant less: the clearing price falls with supply",
      world.entry_gross("zz_entry", 1, 1) > world.entry_gross("zz_entry", 1, 6) > 0.0,
      (world.entry_gross("zz_entry", 1, 1), world.entry_gross("zz_entry", 1, 6)))
check("some firms enter a proven concern", counts[-1] > 0, counts)
check("entry stops by itself with no cap: the last years add no firm", counts[-1] == counts[-11], counts)

_, dear = run_entry(40, rate_scale=40.0)
check("a dearer market rate for capital leaves fewer entrants", dear[-1] < counts[-1], (dear[-1], counts[-1]))

check("the entrant's cost of capital is the capital market's rate", world.market_rate() == game.market_rate())
