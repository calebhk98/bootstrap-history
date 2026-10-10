"""Complaint 106: every borrower pays the market rate plus a premium from its own standing and arrears, and its credit
ceiling is what its earning can carry within what lenders still hold. Pure rate functions, then actors on the fake world."""

QUICK_TOPIC = True

import unittest

from sim.agents.api import ActorRecord, ActorsState
from sim.agents.firm import Firm
from sim.world import capital_market

from .agents_fake_world import FakeWorld

START = 0.12


def firm(state, name, money=0.0, founded_year=100, last_margin=1.0e6):
    actor = Firm(name, ActorRecord(kind="firm", last_margin=last_margin, founded_year=founded_year))
    actor.attach(state.purses)
    actor.money = money
    return actor


class RateFunctions(unittest.TestCase):
    def test_a_borrower_with_no_arrears_and_no_standing_pays_the_market_rate(self):
        self.assertAlmostEqual(capital_market.borrower_rate(START, 0.0, 0.0), START)

    def test_standing_removes_premium(self):
        self.assertLess(capital_market.borrower_rate(START, 0.02, 1.0), capital_market.borrower_rate(START, 0.0, 1.0))

    def test_no_discount_takes_a_rate_below_the_market_rate(self):
        for discount in (0.0, 0.03, 0.5, 10.0):
            for used in (0.0, 0.3, 1.0, 5.0):
                self.assertGreaterEqual(capital_market.borrower_rate(START, discount, used), START - 1e-15)

    def test_arrears_make_money_dearer_up_to_the_ceiling_and_no_further(self):
        self.assertLess(START, capital_market.borrower_rate(START, 0.0, 0.5))
        self.assertLess(capital_market.borrower_rate(START, 0.0, 0.5), capital_market.borrower_rate(START, 0.0, 1.0))
        self.assertEqual(capital_market.borrower_rate(START, 0.0, 3.0), capital_market.borrower_rate(START, 0.0, 1.0))

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


if __name__ == "__main__":
    unittest.main()
