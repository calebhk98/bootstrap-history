"""Complaint 327 (and 412), one rule at a time: a state's money moves between named actors, a surplus no work wants
stays in the reserve, and what the state lends is a claim on borrowers who pay it interest. Each test calls the rule
on inputs it builds: `ledger.transfer`, `Government.build_works` on a stand-in world, `Purses`, and the lendable funds."""

QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.agents import ledger, state_works
from sim.agents.api import Government, Stratum, stratum_id
from sim.agents.edges import EDGE_BUILDERS
from sim.agents.purses import Purses
from sim.agents.records import ActorRecord
from sim.agents.tuning_spending import MASONRY_PERSON_YEARS_PER_M2, RESERVE_CEILING_YEARS_OF_NEED
from sim.finance.api import rules
from sim.finance.constants import LENDABLE_RESERVE_SHARE

from .agents_fake_world import FakeWorld

WAGE = 1000.0


class StateWorld(FakeWorld):
    """A country with no strata in need and no works yet wanted; a test adds a gap."""

    def __init__(self, money):
        super().__init__()
        self.state = Government("government:home", ActorRecord(kind="government", money=money))
        self.strata = []

    def country_strata(self):
        return self.strata

    def government(self):
        return self.state

    def need_floor_costs_per_person_year(self):
        return {"food": 100.0}

    def pay_per_person_year(self, trade):
        return WAGE

    def national_people(self, trade):
        return 1.0e9

    def local_staff(self, trade, people):
        return people


def standing_need_lines(total):
    from sim.agents import budget
    return [budget.Line("army", "requisition", {}, total)]


def surplus_spent(world, gaps):
    """Run the state's surplus spending with the granary and the works wanted fixed by the test."""
    with mock.patch.object(Government, "restock_granary", return_value=0.0), \
            mock.patch.object(state_works, "gaps", return_value=gaps), \
            mock.patch.object(state_works, "held", return_value={"capital_buildings": 0.0}):
        world.state.build_works(standing_need_lines(100.0), world)


class SurplusSpending(unittest.TestCase):
    def test_a_surplus_no_work_wants_stays_in_the_reserve(self):
        world = StateWorld(money=1.0e9)
        surplus_spent(world, [])
        self.assertEqual(world.state.money, 1.0e9)
        self.assertEqual(world.state.record.outlays, {})

    def test_a_work_is_paid_to_the_builders_edge_and_booked_both_sides(self):
        world = StateWorld(money=1.0e9)
        work = state_works.WORKS[-1]
        gap = 10.0
        surplus_spent(world, [(work, gap)])
        paid = gap * MASONRY_PERSON_YEARS_PER_M2 * WAGE
        self.assertAlmostEqual(world.state.record.outlays["building " + work.name], paid)
        self.assertAlmostEqual(world.state.money, 1.0e9 - paid)
        self.assertAlmostEqual(world.edge(EDGE_BUILDERS).balance(), paid)

    def test_nothing_is_spent_while_the_reserve_is_below_its_ceiling(self):
        need = 100.0
        world = StateWorld(money=RESERVE_CEILING_YEARS_OF_NEED * need)
        surplus_spent(world, [(state_works.WORKS[-1], 10.0)])
        self.assertEqual(world.state.record.outlays, {})

    def test_a_work_costs_no_more_than_the_surplus(self):
        need = 100.0
        surplus = 5000.0
        world = StateWorld(money=RESERVE_CEILING_YEARS_OF_NEED * need + surplus)
        surplus_spent(world, [(state_works.WORKS[-1], 1.0e6)])
        self.assertAlmostEqual(sum(world.state.record.outlays.values()), surplus)


class MoneyBetweenActors(unittest.TestCase):
    def test_what_one_actor_pays_another_receives_under_the_same_purpose(self):
        world = StateWorld(money=100.0)
        body = Stratum(stratum_id("home", "poor"), ActorRecord(kind="stratum", stratum="poor", members=1.0, money=0.0))
        ledger.transfer(world.state, body, 40.0, "relief")
        self.assertEqual((world.state.money, body.money), (60.0, 40.0))
        self.assertEqual(world.state.record.outlays, {"relief": 40.0})
        self.assertEqual(body.record.income, {"relief": 40.0})


class LoanableFunds(unittest.TestCase):
    def test_a_state_with_a_reserve_beyond_its_need_offers_a_share_of_it(self):
        spare = rules.state_spare_reserve(1000.0, 400.0, False)
        self.assertEqual(spare, 600.0)
        self.assertAlmostEqual(rules.lendable_share_of_reserve(spare), LENDABLE_RESERVE_SHARE * 600.0)
        self.assertGreater(rules.lendable_share_of_reserve(spare), 0.0)

    def test_a_state_that_cannot_meet_its_need_offers_nothing(self):
        self.assertEqual(rules.state_spare_reserve(1000.0, 400.0, True), 0.0)
        self.assertEqual(rules.state_spare_reserve(300.0, 400.0, False), 0.0)


class LendingThroughThePool(unittest.TestCase):
    def setUp(self):
        self.purses = Purses()
        self.purses.set_net("state", 1000.0, "opening")
        self.purses.set_net("firm", 0.0, "opening")
        self.purses.set_offers({"state": 400.0})

    def test_the_offer_becomes_the_states_deposit(self):
        self.assertAlmostEqual(self.purses.deposit("state"), 400.0)

    def test_what_a_borrower_draws_is_a_claim_held_against_it(self):
        self.purses.cover("firm", 100.0)
        self.assertAlmostEqual(self.purses.debt("firm"), 100.0)
        self.assertAlmostEqual(self.purses.lent(), 100.0)
        self.assertLessEqual(self.purses.lent(), self.purses.offers["state"])

    def test_interest_to_the_state_never_exceeds_what_the_borrower_paid(self):
        self.purses.cover("firm", 100.0)
        self.purses.pay_interest("firm", 10.0)
        received = self.purses.settle_interest()
        self.assertGreater(received["state"], 0.0)
        self.assertLessEqual(sum(received.values()), 10.0 + 1e-9)

    def test_a_state_that_offers_nothing_earns_nothing(self):
        purses = Purses()
        purses.set_net("state", 1000.0, "opening")
        purses.set_net("firm", 0.0, "opening")
        purses.set_offers({})
        purses.cover("firm", 100.0)
        purses.pay_interest("firm", 10.0)
        self.assertNotIn("state", purses.settle_interest())

    def test_the_book_balances_after_lending_and_interest(self):
        self.purses.cover("firm", 100.0)
        self.purses.pay_interest("firm", 10.0)
        self.purses.settle_interest()
        self.assertTrue(self.purses.book.check_conservation(1e-9).ok)


if __name__ == "__main__":
    unittest.main()
