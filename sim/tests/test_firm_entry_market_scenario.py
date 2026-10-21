"""Scenario: Complaint 330, part 1 in a game. The agent economy's `entry_gross` falls as sellers are added, firms enter a proven
concern, and the entrants' cost of capital is the game's market rate. The rules (entry stops by itself, dearer capital
leaves fewer entrants) are in test_firm_entry_market."""
from .harness import *  # noqa: F401,F403

from sim.engine.agents_port import SimWorld

import copy
import random
from unittest import mock

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
NODE = make_node("zz_entry", CATEGORY, revenue=2.2e5, upkeep=5000.0, hours=50.0)


def run_entry(years, rate_scale=1.0):
	"""A game played `years`; capital costs the entrants `rate_scale` times the usual rate (their own cost of
	capital: re-solving every price at another rate is the price solver's work, not under test)."""
	game = actor_sim([NODE])
	game.market_rate = lambda: 0.12
	founder_runs(game, "zz_entry", opened_ago=10)
	counts = []
	with mock.patch.object(SimWorld, "market_rate", lambda self: rate_scale * 0.12):
		for _ in range(years):
			next_year(game)
			counts.append(len(game.actors.active_firms()))
	return game, counts


game, counts = run_entry(8)
world = SimWorld(game)
check("more sellers in a market leave each an entrant less: the clearing price falls with supply",
      world.entry_gross("zz_entry", 1, 1) > world.entry_gross("zz_entry", 1, 6) > 0.0,
      (world.entry_gross("zz_entry", 1, 1), world.entry_gross("zz_entry", 1, 6)))
check("some firms enter a proven concern", counts[-1] > 0, counts)
check("the entrant's cost of capital is the capital market's rate", world.market_rate() == game.market_rate())
