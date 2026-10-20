"""Scenario, Complaint 345 in a game (the rules are in test_firm_count_from_costs): the number of firms in a niche follows what a firm carries (site rent from the
engine's land price while the economy opens, a manager's hours) against what the market pays, with no
cap on entrants a year. Slow topic: it builds games and runs decades.

Re-measure: `python3 -m sim.tests --slow --only firm_count_whole_game_scenario`."""
from .harness import *  # noqa: F401,F403

import copy
import random

from sim.engine.agents_port import SimWorld

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if not node["pre"] and node["cap"] >= 0)
CATEGORY = sorted(S.Sim.GOODS_CATEGORIES)[0]


def make_node(revenue):
	node = copy.deepcopy(NODES[_TEMPLATE_ID])
	node.update(id="zz_count", name="zz_count", traits=["commerce"], pre=[], lab={"labourer": 50.0},
	            mat={}, plant_crew_people=3.0, rev=revenue, up=5000.0, yrs=1.0, risk=0.0, ph=0.0, dev_years=None, dev_people=None, cat=CATEGORY)
	node.pop("gains", None)
	return node


def new_game(revenue):
	nodes = copy.deepcopy(NODES)
	nodes["zz_count"] = make_node(revenue)
	game = build_unopened(lambda: S.Sim(nodes, list(ORDER), random.Random(1), events=False, manual=True,
	             civ=S.load_civ("rome_100ad")))
	game.goal, game.done_year = GOAL, {}
	game.market_rate = lambda: 0.12
	ready_for_entry(game)
	year = game.state.scenario.year
	game.state.projects.done.add("zz_count")
	game.state.projects.done_year["zz_count"] = year - 10
	game.state.projects.operating.add("zz_count")
	game.state.projects.business.set_opened_year("zz_count", year - 10)
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


# a firm's crew is the plant's own (what one plant needs to run), not a share of what the market pays, so the
# firms of every market size are the same size and the count follows the market
MARKET_REVENUES = (6.0e4, 1.2e5, 1.6e5, 2.0e5, 4.0e5)
runs = {revenue: firms_after(revenue, 30) for revenue in MARKET_REVENUES}
small_game, small_counts = runs[2.0e5]
big_game, big_counts = runs[4.0e5]
world = SimWorld(big_game)

check("while the economy opens a concern still pays rent, at the engine's land price",
      world.site_rent("zz_count") > 0.0, world.site_rent("zz_count"))
check("a bigger market holds more firms", big_counts[-1] > small_counts[-1], (small_counts[-1], big_counts[-1]))
check("firms grow no faster than the market they share", big_counts[-1] <= 10.0 * max(1, small_counts[-1]) + 1,
      (small_counts[-1], big_counts[-1]))
check("no cap on entrants a year: some year admits more than one firm to the bigger market",
      any(later - earlier > 1 for earlier, later in zip([0] + big_counts, big_counts)), big_counts)
check("the count settles: the last years add no more than the first",
      big_counts[-1] - big_counts[-6] <= max(big_counts[5], 1), big_counts)

crews = {revenue: SimWorld(game).concern_staff("zz_count") for revenue, (game, _counts) in runs.items()}
check("a firm's crew does not grow with the market", len({tuple(sorted(crew.items())) for crew in crews.values()}) == 1, crews)
final_counts = {revenue: runs[revenue][1][-1] for revenue in MARKET_REVENUES}
# a firm enters at a higher hurdle than the one under which it stays, so a count can sit anywhere in that band
# and two nearby sizes may differ by a firm either way; a market twice the size never holds fewer
check("a market at least twice the size never holds fewer firms",
      all(final_counts[large] >= final_counts[small] for small in MARKET_REVENUES for large in MARKET_REVENUES
          if large >= 2.0 * small), final_counts)
check("the largest market holds more firms than the smallest", final_counts[MARKET_REVENUES[-1]] > final_counts[MARKET_REVENUES[0]], final_counts)

# a concern whose data states a plant is crewed by what its lines ask of staff, whatever its takings
derived_id = next(node_id for node_id in sorted(big_game.nodes)
                  if big_game.nodes[node_id].get("_revenue_basis") == "output"
                  and sum(big_game.nodes[node_id]["_labour_hours_per_year"].values()) > 0.0)
derived_world = SimWorld(big_game)
crew_before = sum(derived_world.concern_staff(derived_id).values())
expected_crew = sum(big_game.nodes[derived_id]["_labour_hours_per_year"].values()) / big_game.HOURS_PER_PERSON_YEAR
big_game.nodes[derived_id]["rev"] *= 3.0
check("a derived concern's crew is its plant's hours over a person-year", abs(crew_before - expected_crew) < 1e-9, (crew_before, expected_crew))
check("...and does not move with its takings", sum(derived_world.concern_staff(derived_id).values()) == crew_before)

# entrants act on what the market pays now, not on a stale expectation that ignores the firms already
# in: the count rises to what the market holds and stays near it, rather than overshooting and collapsing
for revenue, (_game, counts) in sorted(runs.items()):
	settled_count = sorted(counts[-5:])[2]
	check("entry does not overshoot what the market holds (market %g)" % revenue,
	      max(counts) <= 3 * max(1, settled_count) + 2, counts)
