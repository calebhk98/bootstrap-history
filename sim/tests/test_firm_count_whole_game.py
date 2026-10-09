"""Complaint 345, whole game: the number of firms in a niche follows what a firm carries (site rent from the
engine's land price while the agent economy is off, a manager's hours) against what the market pays, with no
cap on entrants a year. Slow topic: it builds games and runs decades.

Re-measure: `python3 -m sim.tests --slow --only firm_count_whole_game`."""
from .harness import *  # noqa: F401,F403

import copy
import random

from sim.engine.agents_port import SimWorld

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if node["rev"] > 0 and not node["pre"] and node["cap"] >= 0)
CATEGORY = sorted(S.Sim.GOODS_CATEGORIES)[0]


def make_node(revenue):
	node = copy.deepcopy(NODES[_TEMPLATE_ID])
	node.update(id="zz_count", name="zz_count", traits=["commerce"], pre=[], lab={"labourer": 50.0},
	            mat={}, rev=revenue, up=5000.0, yrs=1.0, risk=0.0, ph=0.0, dev_years=None, dev_people=None, cat=CATEGORY)
	node.pop("gains", None)
	return node


def new_game(revenue):
	nodes = copy.deepcopy(NODES)
	nodes["zz_count"] = make_node(revenue)
	game = S.Sim(nodes, list(ORDER), random.Random(1), events=False, manual=True,
	             civ=S.load_civ("rome_100ad"), cfg={"agent_economy": False})
	game.goal, game.done_year = GOAL, {}
	game.market_rate = lambda: 0.12
	year = game.state.scenario.year
	game.state.projects.done.add("zz_count")
	game.state.projects.done_year["zz_count"] = year - 10
	game.state.projects.operating.add("zz_count")
	game.state.projects.opened_year["zz_count"] = year - 10
	game._done_changed()
	return game


def next_year(game):
	game.state.scenario.year += 1
	game.advance_actors(game.state.scenario.year)


def firms_after(revenue, years):
	game = new_game(revenue)
	counts = []
	for _ in range(years):
		next_year(game)
		counts.append(len(game.actors.active_firms()))
	return game, counts


small_game, small_counts = firms_after(2.0e5, 30)
big_game, big_counts = firms_after(2.0e6, 30)
world = SimWorld(big_game)

check("with the agent economy off a concern still pays rent, at the engine's land price",
      world.site_rent("zz_count") > 0.0, world.site_rent("zz_count"))
check("a bigger market holds more firms", big_counts[-1] > small_counts[-1], (small_counts[-1], big_counts[-1]))
check("firms grow no faster than the market they share", big_counts[-1] <= 10.0 * max(1, small_counts[-1]) + 1,
      (small_counts[-1], big_counts[-1]))
check("no cap on entrants a year: some year admits more than one firm to the bigger market",
      any(later - earlier > 1 for earlier, later in zip([0] + big_counts, big_counts)), big_counts)
check("the count settles: the last years add no more than the first",
      big_counts[-1] - big_counts[-6] <= max(big_counts[5], 1), big_counts)
