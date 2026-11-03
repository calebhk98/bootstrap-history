"""Complaint 106: every borrower pays the market rate plus a premium from its own standing and arrears, and its credit
ceiling is what its earning can carry within what lenders still hold. Pure rate functions, then actors on the fake world."""

QUICK_TOPIC = True

import unittest

from sim.agents.api import ActorRecord, ActorsState
from sim.agents.firm import Firm
from sim.world import capital_market

from .agents_fake_world import FakeWorld
from .pool_lenders import lend_from_savers, lend_through

START = 0.12


def firm(state, name, money=0.0, founded_year=100, last_margin=1.0e6):
    actor = Firm(name, ActorRecord(kind="firm", last_margin=last_margin, founded_year=founded_year))
    actor.attach(state.purses)
    actor.money = money
    return actor


class RateFunctions(unittest.TestCase):
    def test_what_is_left_to_lend_is_never_negative(self):
        self.assertEqual(capital_market.headroom(100.0, 30.0), 70.0)
        self.assertEqual(capital_market.headroom(100.0, 130.0), 0.0)

    def test_the_debt_an_earning_can_carry_falls_as_the_rate_rises(self):
        self.assertGreater(capital_market.serviceable_debt(100.0, 0.05, 0.5), capital_market.serviceable_debt(100.0, 0.10, 0.5))
        self.assertEqual(capital_market.serviceable_debt(100.0, 0.0, 0.5), 0.0)


class ActorsBorrowByOneMethod(unittest.TestCase):
    def setUp(self):
        self.state = ActorsState()
        self.world = FakeWorld()
        self.world.edge_book = self.state
        self.world.rate = START
        lend_from_savers(self.state.purses, 1e12)

    def test_two_firms_with_the_same_record_and_no_debt_borrow_at_the_same_rate(self):
        first, second = firm(self.state, "a"), firm(self.state, "b")
        self.assertAlmostEqual(first.borrowing_rate(self.world), second.borrowing_rate(self.world))

    def test_a_firm_in_arrears_pays_more_than_a_sound_one(self):
        first, second = firm(self.state, "a"), firm(self.state, "b")
        second.money = -0.5 * second.credit_ceiling(self.world)
        self.assertGreater(second.borrowing_rate(self.world), first.borrowing_rate(self.world))

    def test_a_firm_with_a_longer_record_in_the_same_arrears_pays_less_premium(self):
        unproven = firm(self.state, "c", founded_year=self.world.year)
        proven = firm(self.state, "d", founded_year=self.world.year - 30)
        for each in (unproven, proven):
            each.money = -0.5 * each.credit_ceiling(self.world)
        self.assertLess(proven.borrowing_rate(self.world), unproven.borrowing_rate(self.world))

    def test_the_ceiling_is_what_earning_carries_within_what_lenders_hold(self):
        actor = firm(self.state, "a")
        self.assertGreater(actor.credit_ceiling(self.world), 0.0)
        self.world.credit_headroom = lambda actor_id: 10.0
        self.assertEqual(actor.credit_ceiling(self.world), 10.0)

    def test_a_firm_in_debt_pays_interest_booked_by_purpose_and_added_to_the_debt(self):
        debtor = firm(self.state, "e", money=-1.0e5)
        owed = debtor.pay_interest(self.world)
        self.assertGreater(owed, 0.0)
        self.assertEqual(debtor.record.outlays.get("interest"), owed)
        self.assertAlmostEqual(debtor.money, -1.0e5 - owed)
        self.assertGreater(self.world.interest_paid, 0.0)

    def test_a_firm_with_no_debt_pays_nothing(self):
        self.assertEqual(firm(self.state, "f", money=500.0).pay_interest(self.world), 0.0)


class DrawLimit(unittest.TestCase):
    """Borrower.rule_limit: one rule for every borrower, the economy's (design D1); draw_limit adds what the lenders can supply."""
    def setUp(self):
        self.state = ActorsState()
        self.world = FakeWorld()
        self.world.edge_book = self.state
        self.world.rate = START
        lend_from_savers(self.state.purses, 1e12)
        self.actor = firm(self.state, "a")
        self.ceiling = self.actor.credit_ceiling(self.world)

    def test_a_draw_inside_the_ceiling_is_the_whole_draw_while_the_market_has_not_met(self):
        self.assertEqual(self.actor.rule_limit(self.world, 0.5 * self.ceiling), 0.5 * self.ceiling)

    def test_a_draw_past_the_ceiling_is_cut_to_what_the_ceiling_leaves(self):
        self.actor.money = -0.25 * self.ceiling
        self.assertAlmostEqual(self.actor.rule_limit(self.world, 10.0 * self.ceiling), 0.75 * self.ceiling)

    def test_the_economys_fundable_amount_cuts_the_draw_further(self):
        asked = []
        self.world.fundable_amount = lambda amount, debt, collateral, arrears: asked.append((amount, debt, collateral, arrears)) or 7.0
        self.assertEqual(self.actor.rule_limit(self.world, 0.5 * self.ceiling), 7.0)
        self.assertEqual(asked, [(0.5 * self.ceiling, 0.0, self.ceiling, 0.0)])

    def test_the_draw_limit_is_the_rules_limit_cut_to_what_the_lenders_can_supply(self):
        lend_through(self.state.purses, {"cohort:small": (30.0, 0.05)}, coin_per_unit=1.0)   # replaces the lenders: 30 coin on offer
        self.assertEqual(self.actor.rule_limit(self.world, 100.0), 100.0)
        self.assertAlmostEqual(self.actor.draw_limit(self.world, 100.0), 30.0)

    def test_an_actor_with_nothing_to_show_lenders_draws_nothing(self):
        self.assertEqual(firm(self.state, "b", last_margin=0.0).rule_limit(self.world, 100.0), 0.0)

    def test_the_rate_on_a_draw_is_the_market_rate_plus_the_economys_premium(self):
        self.world.risk_premium = lambda debt_after, collateral, arrears: 0.04
        free_of_standing = firm(self.state, "c", founded_year=self.world.year)
        free_of_standing.credit_standing = lambda world: 0.0
        self.assertAlmostEqual(free_of_standing.rate_on_loan(self.world, 10.0), START + 0.04)

    def test_standing_takes_only_premium_off_the_rate(self):
        self.world.risk_premium = lambda debt_after, collateral, arrears: 0.0
        self.actor.credit_standing = lambda world: 1.0
        self.assertAlmostEqual(self.actor.rate_on_loan(self.world, 10.0), START)


if __name__ == "__main__":
    unittest.main()
