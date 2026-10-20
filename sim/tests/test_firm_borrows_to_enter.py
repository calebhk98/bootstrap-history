"""Complaint 308: a firm borrows through the capital market to enter and to pay for copying, not only to
expand. When the founder's savings cannot fund an entrant's whole stake, the rest is raised as credit bounded by
the entrant's expected earning, at the borrower's rate, provided the founder puts up their share of it.

A founder is a stratum's best-placed household (`household_wealth.personal_capital`), and the strata's purses
refill every year in a game, so how much a founder can put up is set by wrapping `firm_entry.personal_capital`
with a ceiling. The ceilings are taken from the stake an unconstrained founder puts up and the share lenders
require (`ENTRY_EQUITY_SHARE`). Years are few: the claims are about who enters and what they owe."""
from .harness import *  # noqa: F401,F403

from sim.engine.agents_port import SimWorld
from sim.agents import firm_entry
from sim.agents.tuning import ENTRY_EQUITY_SHARE
from sim.engine.state import ActorRecord
from sim.agents.firm import Firm

import copy
import random
from unittest import mock

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if not node["pre"] and node["cap"] >= 0)


def make_node(node_id, category, revenue, upkeep, hours):
	node = copy.deepcopy(NODES[_TEMPLATE_ID])
	node.update(id=node_id, name=node_id, traits=["commerce"], pre=[], lab={"labourer": hours},
	            mat={}, rev=revenue, up=upkeep, yrs=1.0, risk=0.0, ph=0.0,
	            dev_years=None, dev_people=None, cat=category)
	node.pop("gains", None)
	return node


def actor_sim():
	nodes = copy.deepcopy(NODES)
	nodes["zz_borrow"] = make_node("zz_borrow", sorted(S.Sim.GOODS_CATEGORIES)[0], 8.0e5, 5000.0, 50.0)
	game = build_unopened(lambda: S.Sim(nodes, list(ORDER), random.Random(1), events=False, manual=True,
	             civ=S.load_civ("rome_100ad")))
	game.goal, game.done_year = GOAL, {}
	game.market_rate = lambda: 0.12
	year = game.state.scenario.year
	projects = game.state.projects
	projects.done.add("zz_borrow")
	projects.done_year["zz_borrow"] = year - 10
	projects.operating.add("zz_borrow")
	projects.business.set_opened_year("zz_borrow", year - 10)
	game._done_changed()
	return ready_for_entry(game)


_PUT_UP = firm_entry.personal_capital
_STAKE_SPLIT = firm_entry.stake_split
faced = []   # every stake an entrant weighed, in the order weighed


def _recording_stake_split(stake, *args):
	faced.append(stake)
	return _STAKE_SPLIT(stake, *args)


def run(ceiling=None, credit_rate=None, years=6):
	"""A game played `years`, in which no founder puts up more than `ceiling` and the firms' cost of capital is
	`credit_rate` (the firms' own: re-solving every price at another rate is not under test).
	Returns (game, firms each year, the deepest debt of any firm, the stakes founders put up)."""
	game = actor_sim()
	patches = [mock.patch.object(firm_entry, "stake_split", _recording_stake_split)]
	if ceiling is not None:
		patches.append(mock.patch.object(firm_entry, "personal_capital", lambda stratum: min(_PUT_UP(stratum), ceiling)))
	if credit_rate is not None:
		patches.append(mock.patch.object(SimWorld, "market_rate", lambda self: credit_rate))
	counts, deepest_debt = [], 0.0
	for patch in patches:
		patch.start()
	try:
		for _ in range(years):
			game.state.scenario.year += 1
			game.advance_actors(game.state.scenario.year)
			counts.append(len(game.actors.active_firms()))
			for firm in game.actors.active_firms():
				deepest_debt = max(deepest_debt, firm.debt())
	finally:
		for patch in patches:
			patch.stop()
	stakes = [firm.record.plan["stake"] for firm in game.actors.active_firms() if "stake" in firm.record.plan]
	return game, counts, deepest_debt, stakes


_funded_game, funded_counts, _debt, funded_stakes = run()
whole_stake = max(funded_stakes)
check("a founder who can put up the whole stake founds firms beyond the opening ones",
      max(funded_counts) > funded_counts[0] and whole_stake > 0.0, (funded_counts, whole_stake))

short = 1.05 * ENTRY_EQUITY_SHARE * whole_stake   # more than lenders' share of the stake, so little over it that the entrant must borrow
unfunded, short_counts, borrowed, short_stakes = run(ceiling=short)
check("a founder short of the whole stake but putting up lenders' share still founds firms, on credit",
      max(short_counts) > short_counts[0] and bool(short_stakes) and max(short_stakes) <= short + 1e-6 < whole_stake,
      (short_counts, short_stakes, short, whole_stake))
check("an entrant that borrowed owes the market", borrowed > 0.0, borrowed)

# Under lenders' share of the stake: no one backs the entrant. The stake an entrant weighs falls as the concern
# ages (the early years' losses it must carry shrink), so "the stake" is the smallest one weighed in the funded run.
thin = 0.5 * ENTRY_EQUITY_SHARE * min(faced)
_thin_game, thin_counts, _thin_debt, thin_stakes = run(ceiling=thin)
check("a founder putting up less than lenders' share founds no firm from savings (only the opening ones stand)",
      max(thin_counts) == thin_counts[0] and not thin_stakes, (thin_counts, thin_stakes))

_dear_game, dear_counts, _dear_debt, _stakes = run(ceiling=short, credit_rate=2.0)
check("dearer credit leaves fewer entrants on credit", max(dear_counts) < max(short_counts), (dear_counts, short_counts))

# a firm's copy budget counts what it may still borrow
world = SimWorld(unfunded)
firm = Firm("zz", ActorRecord(kind="firm", last_margin=1.0e5, founded_year=world.year))
check("a firm with no money may still budget what its earning lets it borrow", firm.copy_budget(world) > 0.0,
      firm.copy_budget(world))
firm.record.last_margin = 0.0
check("a firm with no earning has no copy budget on credit", firm.copy_budget(world) == 0.0)
