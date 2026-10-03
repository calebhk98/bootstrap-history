"""Complaint 308: a firm borrows through the capital market to enter and to pay for copying, not only to
expand. When the pooled capital cannot fund an entrant's stake, the founder raises the rest as credit
bounded by the entrant's expected earning, at the borrower's rate."""
from .harness import *  # noqa: F401,F403

from sim.agents.api import SimWorld
from sim.agents import registry as actor_registry
from sim.engine.state import ActorRecord
from sim.agents.firm import Firm

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


def actor_sim(rate):
	nodes = copy.deepcopy(NODES)
	nodes["zz_borrow"] = make_node("zz_borrow", sorted(S.Sim.GOODS_CATEGORIES)[0], 2.0e5, 5000.0, 50.0)
	game = S.Sim(nodes, list(ORDER), random.Random(1), events=False, manual=True,
	             civ=S.load_civ("rome_100ad"))
	game.goal, game.done_year = GOAL, {}
	game.market_rate = lambda: rate
	year = game.state.scenario.year
	projects = game.state.projects
	projects.done.add("zz_borrow")
	projects.done_year["zz_borrow"] = year - 10
	projects.operating.add("zz_borrow")
	projects.opened_year["zz_borrow"] = year - 10
	game._done_changed()
	return game


def run(rate, pooled_share, years=30):
	original = actor_registry.ENTREPRENEURIAL_CAPITAL_SHARE
	actor_registry.ENTREPRENEURIAL_CAPITAL_SHARE = pooled_share
	try:
		game = actor_sim(rate)
		deepest_debt = 0.0
		for _ in range(years):
			game.state.scenario.year += 1
			game.advance_actors(game.state.scenario.year)
			for firm in game.actors.active_firms():
				deepest_debt = max(deepest_debt, firm.debt())
		return game, deepest_debt
	finally:
		actor_registry.ENTREPRENEURIAL_CAPITAL_SHARE = original


funded, _debt = run(0.12, actor_registry.ENTREPRENEURIAL_CAPITAL_SHARE)
check("with the pooled capital the usual firms enter", len(funded.actors.active_firms()) > 0)

unfunded, borrowed = run(0.12, 0.0)
check("with no pooled capital firms still enter, on credit", len(unfunded.actors.active_firms()) > 0,
      len(unfunded.actors.active_firms()))
check("an entrant that borrowed owes the market", borrowed > 0.0, borrowed)

dear, _dear_debt = run(40.0 * 0.12, 0.0)
check("dearer credit leaves fewer entrants on credit",
      len(dear.actors.active_firms()) < len(unfunded.actors.active_firms()),
      (len(dear.actors.active_firms()), len(unfunded.actors.active_firms())))

# a firm's copy budget counts what it may still borrow
world = SimWorld(unfunded)
firm = Firm("zz", ActorRecord(kind="firm", last_margin=1.0e5, founded_year=world.year))
check("a firm with no money may still budget what its earning lets it borrow", firm.copy_budget(world) > 0.0,
      firm.copy_budget(world))
firm.record.last_margin = 0.0
check("a firm with no earning has no copy budget on credit", firm.copy_budget(world) == 0.0)
