"""Complaints 620 and 600: what a concern must carry grows with what it sells. When the economy
grows and labour is the scarce input a concern's wage bill grows with it, its running costs follow
the volume it sells, a category's takings are the market's own price times volume shared out, and
the number of firms in a niche is set by the market's size over a firm's, so it stops growing when
the market stops growing."""
from .harness import *  # noqa: F401,F403

from sim.engine.actors import SimWorld

import copy
import random

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
NODE = make_node("zz_scale", CATEGORY, revenue=2.0e5, upkeep=5000.0, hours=50.0)


def settled(growth=1.0, years=40, rate=0.12):
	game = actor_sim([NODE])
	game.market_rate = lambda: rate
	founder_runs(game, "zz_scale", opened_ago=10)
	for _ in range(years):
		next_year(game)
	game.state.economy.economy *= growth
	for _ in range(years):
		next_year(game)
	return game


# ---- labour is the scarce input: a richer economy pays more an hour -------------------------------
game = actor_sim([NODE])
founder_runs(game, "zz_scale", opened_ago=10)
next_year(game)
world = SimWorld(game)
wage_before = world.concern_wage_bill("zz_scale")
hour_before = world.wage_per_hour("labourer")
output_before = world.society_output()
founder_wage_before = game.annual_wage("artisan")
game.state.economy.economy *= 10.0
game._revenue_cache_key = None
world = SimWorld(game)
check("when the economy grows a concern's wage bill grows with it",
      world.concern_wage_bill("zz_scale") > 2.0 * wage_before, (wage_before, world.concern_wage_bill("zz_scale")))
check("the wage an hour of labour earns rises with output per hour",
      world.wage_per_hour("labourer") > 2.0 * hour_before, (hour_before, world.wage_per_hour("labourer")))
check("what the society makes follows its wage, so a growing economy makes more",
      world.society_output() > 2.0 * output_before, (output_before, world.society_output()))
check("the founder's staff are paid on the same terms as a firm's",
      game.annual_wage("artisan") > 2.0 * founder_wage_before, (founder_wage_before, game.annual_wage("artisan")))

# ---- running costs follow the volume a concern sells ---------------------------------------------
game = actor_sim([NODE])
founder_runs(game, "zz_scale", opened_ago=10)
next_year(game)
world = SimWorld(game)
upkeep_before = world.upkeep("zz_scale")
margin_ratio_before = (world.concern_takings("zz_scale", game.year - 10) - upkeep_before) / upkeep_before
game.state.economy.economy *= 10.0
world = SimWorld(game)
check("the upkeep of a concern that earns rises with the volume it sells",
      world.upkeep("zz_scale") > 2.0 * upkeep_before, (upkeep_before, world.upkeep("zz_scale")))
check("the founder pays the same upkeep an actor does for the same concern",
      abs(game.venture_real_upkeep("zz_scale") - world.upkeep("zz_scale")) < 1e-6 * world.upkeep("zz_scale"))
margin_ratio_after = (world.concern_takings("zz_scale", game.year - 10) - world.upkeep("zz_scale")) / world.upkeep("zz_scale")
check("a bigger market does not by itself make a concern's takings dwarf its costs",
      margin_ratio_after < 2.0 * margin_ratio_before + 1.0, (margin_ratio_before, margin_ratio_after))

# ---- a category's takings are its market's price times volume, shared out ------------------------
shared = settled()
world = SimWorld(shared)
sellers = len(shared.actors.active_firms()) + 1
ratios = shared._goods_category_ratios(CATEGORY)
volume_scale = shared.state.economy.economy ** shared.ECONOMY_OUTPUT_SCALING_EXPONENT
market_total = (NODE["rev"] * volume_scale * shared.state.economy.output_factor * shared.price_index
                * ratios[0] * ratios[1] * shared.income_factor())
each = world.concern_takings("zz_scale", shared.year - 20)
check("every seller's takings are one share of the market's price times volume",
      abs(each * ratios[2] - market_total) < 0.02 * market_total, (each, ratios, market_total))

# ---- the number of firms follows the market's size over a firm's ---------------------------------
steady = settled(growth=1.0)
grown = settled(growth=10.0)
steady_count = len(steady.actors.active_firms())
grown_count = len(grown.actors.active_firms())
check("firms entered the niche", steady_count > 0, steady_count)
check("a market ten times the economy does not hold ten times the firms",
      grown_count < 4 * max(1, steady_count), (steady_count, grown_count))
count = len(grown.actors.active_firms())
for _ in range(15):
	next_year(grown)
check("a niche whose market stopped growing stops gaining firms", len(grown.actors.active_firms()) == count,
      (count, len(grown.actors.active_firms())))
