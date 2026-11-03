"""A bond sold below face and redeemed at face: the discount is the depositors' return, so it joins the interest the pool
shares out and does not sit in the pool unowned. Called on a `BondBook` and a `Purses` built here."""

QUICK_TOPIC = True

import unittest

from sim.agents.bonds import Bond, BondBook
from sim.agents.purses import COIN, EDGE_OUTSIDE, POOL, Purses
from sim.book import Transfer

from .pool_lenders import lend_from_savers


class BondDiscount(unittest.TestCase):
    def test_retiring_due_bonds_answers_their_discount(self):
        book = BondBook()
        book.held["state"] = [Bond(face=100.0, coupon=0.05, years_left=0.0, paid=80.0), Bond(face=50.0, coupon=0.05, years_left=3.0, paid=40.0)]
        self.assertAlmostEqual(book.retire_due("state"), 20.0)
        self.assertEqual(len(book.held["state"]), 1)

    def test_redeeming_adds_the_discount_to_the_interest_the_pool_shares(self):
        purses = Purses()
        lend_from_savers(purses, 1e9)
        purses.book.transfer(Transfer(EDGE_OUTSIDE, "state", COIN, 500.0, "seed"))
        purses.bonds.held["state"] = [Bond(face=100.0, coupon=0.05, years_left=1.0, paid=80.0)]
        purses.redeem_bonds("state")
        self.assertAlmostEqual(purses.interest_pending, 20.0)


if __name__ == "__main__":
    unittest.main()
