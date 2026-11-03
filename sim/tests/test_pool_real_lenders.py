"""The actors' pool lends only what the economy's lenders hold: a draw beyond the borrower's limit or the lenders' funds is refused
and moves nothing; funds are taken cheapest ask first across the exchange without losing value; interest returns to the lenders in
the economy's unit; a bond that cannot be paid stays on the book."""

QUICK_TOPIC = True

import unittest

from sim.agents.bonds import Bond
from sim.agents.purses import EDGE_OUTSIDE, Purses
from sim.book import InsufficientFunds

from .pool_lenders import UNIT, lend_through, value


def with_lenders(lenders, coin_per_unit=2.0):
    purses = Purses()
    lend_through(purses, lenders, coin_per_unit)
    return purses


class PoolRealLenders(unittest.TestCase):
    def test_cover_with_a_zero_limit_and_an_empty_pool_raises_and_leaves_the_book_unchanged(self):
        purses = with_lenders({"cohort:a": (100.0, 0.05)})
        purses.limit = lambda account, amount: 0.0
        before = purses.book.to_record()
        with self.assertRaises(InsufficientFunds):
            purses.cover("firm:1", 10.0)
        self.assertEqual(purses.book.to_record(), before)
        self.assertEqual(purses.debt("firm:1"), 0.0)

    def test_cover_beyond_what_the_lenders_hold_raises_and_leaves_the_book_unchanged(self):
        purses = with_lenders({"cohort:a": (10.0, 0.05)})   # 10 units are 20 coin
        before = purses.book.to_record()
        with self.assertRaises(InsufficientFunds):
            purses.cover("firm:1", 25.0)
        self.assertEqual(purses.book.to_record(), before)

    def test_cover_with_no_lenders_listed_raises(self):
        purses = Purses()
        with self.assertRaises(InsufficientFunds):
            purses.cover("firm:1", 1.0)

    def test_cover_takes_from_the_cheapest_ask_first_and_conserves_value_through_the_exchange(self):
        purses = with_lenders({"cohort:dear": (100.0, 0.08), "cohort:cheap": (100.0, 0.05)})
        total = value(purses)
        purses.cover("firm:1", 250.0)   # 125 units: all of the cheap lender's 100 and 25 of the dear one's
        self.assertAlmostEqual(purses.book.balance("cohort:cheap", UNIT), 0.0)
        self.assertAlmostEqual(purses.book.balance("cohort:dear", UNIT), 75.0)
        self.assertAlmostEqual(purses.purse("firm:1"), 250.0)
        self.assertAlmostEqual(purses.deposit("cohort:cheap"), 200.0)
        self.assertAlmostEqual(purses.deposit("cohort:dear"), 50.0)
        self.assertAlmostEqual(value(purses), total)

    def test_a_lender_asks_no_more_than_it_offered_beyond_what_it_has_in_the_pool(self):
        purses = with_lenders({"cohort:a": (50.0, 0.05)})
        purses.cover("firm:1", 60.0)   # 30 of its 50 units are in the pool now
        with self.assertRaises(InsufficientFunds):
            purses.cover("firm:2", 50.0)   # 20 units (40 coin) are left on offer
        purses.cover("firm:2", 40.0)
        self.assertAlmostEqual(purses.deposit("cohort:a"), 100.0)

    def test_interest_reaches_the_cohort_lender_in_units_and_its_deposit_returns_when_repaid(self):
        purses = with_lenders({"cohort:a": (100.0, 0.05)})
        purses.cover("firm:1", 100.0)
        purses.pay_interest("firm:1", 10.0)   # the borrower draws the interest too: it owes 110 and the lender has lent 55 units
        purses.transfer(EDGE_OUTSIDE, "firm:1", 110.0, "takings")   # its takings repay the facility
        received = purses.settle_interest()
        self.assertAlmostEqual(received["cohort:a"], 10.0)   # coin
        self.assertAlmostEqual(purses.book.balance("cohort:a", UNIT), 45.0 + 5.0 + 55.0)   # kept, interest in units, deposit back
        self.assertAlmostEqual(purses.deposit("cohort:a"), 0.0)

    def test_redeem_keeps_a_due_bond_as_debt_when_the_payment_is_refused(self):
        purses = Purses()
        purses.bonds.set_terms("state", 0.05, 0.05)
        purses.bonds.held["state"] = [Bond(face=100.0, coupon=0.05, years_left=1.0, paid=95.0)]
        paid = purses.redeem_bonds("state")   # the state holds nothing and no lender is listed
        self.assertEqual(paid, 0.0)
        self.assertAlmostEqual(purses.bonds.debt("state"), 100.0)
