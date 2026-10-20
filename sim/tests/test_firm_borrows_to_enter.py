"""Complaint 308: a firm borrows through the capital market to enter and to pay for copying, not only to
expand. When the founder's savings cannot fund an entrant's whole stake, the rest is raised as credit bounded by
the entrant's expected earning, at the borrower's rate, provided the founder puts up their share of it.

Rules, each called on built inputs (no game):

1. `firm_entry.stake_split`: what a founder puts up, what is left to borrow, and the refusal below lenders' share.
2. `ActorRegistry.consider_entry` on the fake world: a founder short of the whole stake founds on credit, one
   putting up less than lenders' share founds none, and dearer credit leaves fewer entrants on credit.
3. `Firm.copy_budget`: counts what the firm's earning lets it borrow.

The whole-game wiring is `test_firm_borrows_to_enter_scenario`."""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.agents import firm_entry
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents.firm import Firm
from sim.agents.tuning import ENTRY_EQUITY_SHARE

from .agents_fake_world import FakeWorld, make_node

COPY_COST = 6000.0


class EntryWorld(FakeWorld):
	"""A proven concern whose takings are shared among its sellers, with a dear copy."""

	def entry_gross(self, node_id, rivals, entrants):
		return float(self.nodes[node_id]["rev"]) / (rivals + entrants)

	def plant_cost(self, node_id, actor, step):
		return 1000.0 * step

	def ramp(self, opened_year, node_id=None):
		return min(1.0, (self.year - opened_year + 1) / 5.0)


def make_world(rate=0.12):
	world = EntryWorld()
	world.rate = rate
	world.nodes["shop"] = make_node("shop", hours=100.0, revenue=60000.0, upkeep=1000.0)
	world.nodes["shop"]["cost"] = COPY_COST
	world.demonstrated_nodes = {"shop"}
	world.proven = {"shop"}
	return world


class StakeSplitTests(unittest.TestCase):
	def split(self, stake, savings):
		with mock.patch.object(firm_entry, "personal_capital", lambda stratum: savings):
			return firm_entry.stake_split(stake, object(), True, 0.0)

	def test_a_founder_who_can_put_up_the_whole_stake_borrows_nothing(self):
		self.assertEqual(self.split(100.0, 250.0), (100.0, 0.0))

	def test_a_founder_putting_up_lenders_share_borrows_the_rest(self):
		put_up = 1.05 * ENTRY_EQUITY_SHARE * 100.0
		pooled, borrowed = self.split(100.0, put_up)
		self.assertAlmostEqual(pooled, put_up)
		self.assertAlmostEqual(borrowed, 100.0 - put_up)

	def test_a_founder_putting_up_less_than_lenders_share_is_refused_credit(self):
		pooled, borrowed = self.split(100.0, 0.5 * ENTRY_EQUITY_SHARE * 100.0)
		self.assertEqual(borrowed, float("inf"))

	def test_without_strata_the_pooled_capital_funds_up_to_its_limit(self):
		self.assertEqual(firm_entry.stake_split(100.0, None, False, 30.0), (30.0, 70.0))
		self.assertEqual(firm_entry.stake_split(100.0, None, False, 500.0), (100.0, 0.0))


class EntryOnCreditTests(unittest.TestCase):
	def entry(self, ceiling=None, rate=0.12):
		"""(firms founded, stakes weighed, stakes put up) in one year of entry when no founder puts up more than `ceiling`."""
		registry = ActorRegistry(ActorsState(home_country="home"))
		registry.add("stratum:home:merchants", ActorRecord(
			kind="stratum", stratum="merchants", members=100.0, money=1.0e9, literacy=0.5))
		faced = []
		put_up = firm_entry.personal_capital
		split = firm_entry.stake_split

		def recording_split(stake, *arguments):
			faced.append(stake)
			return split(stake, *arguments)

		with mock.patch.object(firm_entry, "stake_split", recording_split), \
				mock.patch.object(firm_entry, "personal_capital",
				                  (lambda stratum: put_up(stratum)) if ceiling is None
				                  else (lambda stratum: min(put_up(stratum), ceiling))):
			founded = registry.consider_entry(make_world(rate))
		stakes = [registry.actors[firm_id].record.plan["stake"] for firm_id in founded
		          if "stake" in registry.actors[firm_id].record.plan]
		return founded, faced, stakes

	def test_a_founder_who_can_put_up_the_whole_stake_founds_firms(self):
		founded, faced, stakes = self.entry()
		self.assertTrue(founded)
		self.assertGreater(max(stakes), 0.0)

	def test_a_founder_short_of_the_whole_stake_but_putting_up_lenders_share_founds_on_credit(self):
		_, faced, _ = self.entry()
		short = 1.05 * ENTRY_EQUITY_SHARE * min(faced)
		founded, _, stakes = self.entry(ceiling=short)
		self.assertTrue(founded)
		self.assertLessEqual(max(stakes), short + 1e-6)
		self.assertLess(short, min(faced))

	def test_a_founder_putting_up_less_than_lenders_share_founds_nothing(self):
		_, faced, _ = self.entry()
		founded, _, stakes = self.entry(ceiling=0.5 * ENTRY_EQUITY_SHARE * min(faced))
		self.assertEqual(founded, [])
		self.assertEqual(stakes, [])

	def test_dearer_credit_leaves_fewer_entrants_on_credit(self):
		_, faced, _ = self.entry()
		short = 1.05 * ENTRY_EQUITY_SHARE * min(faced)
		usual, _, _ = self.entry(ceiling=short, rate=0.12)
		dear, _, _ = self.entry(ceiling=short, rate=2.0)
		self.assertLess(len(dear), len(usual))


class CopyBudgetTests(unittest.TestCase):
	def firm(self, last_margin):
		state = ActorsState(home_country="home")
		firm = Firm("zz", ActorRecord(kind="firm", last_margin=last_margin, founded_year=100))
		firm.attach(state.purses)
		return firm

	def test_a_firm_with_no_money_may_still_budget_what_its_earning_lets_it_borrow(self):
		self.assertGreater(self.firm(1.0e5).copy_budget(make_world()), 0.0)

	def test_a_firm_with_no_earning_has_no_copy_budget_on_credit(self):
		self.assertEqual(self.firm(0.0).copy_budget(make_world()), 0.0)


if __name__ == "__main__":
	unittest.main()
