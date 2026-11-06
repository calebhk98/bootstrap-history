"""A depositor taking its deposit back from a pool that has lent it out: the pool refills only from the lenders it is offered, as far as
they can, and what no lender refills stays deposited."""

QUICK_TOPIC = True

import unittest

from sim.agents.purses import COIN, EDGE_OUTSIDE, Purses
from sim.book import Transfer

from .pool_lenders import UNIT, lend_through


def lent_out_pool(offered_units):
    """firm:1 has 30 coin deposited, all of it lent to firm:2; `offered_units` of the economy's unit (2 coin each) are on offer."""
    purses = Purses()
    purses.book.transfer(Transfer(EDGE_OUTSIDE, "firm:1", COIN, 30.0, "seed"))
    purses.set_offers({"firm:1": 30.0})
    purses.transfer("firm:2", "firm:3", 30.0, "test")   # firm:2 draws the whole pool
    if offered_units:
        lend_through(purses, {"cohort:a": (offered_units, 0.05)}, 2.0)
    else:
        purses.lenders_for = lambda account, amount: (UNIT, 2.0, [])
    return purses


class TakeBack(unittest.TestCase):
    def test_with_no_lender_offered_the_depositor_takes_back_only_what_the_pool_holds_free(self):
        purses = lent_out_pool(0.0)
        purses.set_offers({})
        self.assertAlmostEqual(purses.purse("firm:1"), 0.0)
        self.assertAlmostEqual(purses.deposit("firm:1"), 30.0)

    def test_the_offered_lenders_refill_part_of_it_and_the_rest_stays_deposited(self):
        purses = lent_out_pool(10.0)   # 10 units are 20 coin
        purses.set_offers({})
        self.assertAlmostEqual(purses.purse("firm:1"), 20.0)
        self.assertAlmostEqual(purses.deposit("firm:1"), 10.0)

    def test_lenders_offering_more_than_the_deposit_refill_it_whole(self):
        purses = lent_out_pool(100.0)
        purses.set_offers({})
        self.assertAlmostEqual(purses.purse("firm:1"), 30.0)
        self.assertAlmostEqual(purses.deposit("firm:1"), 0.0)


if __name__ == "__main__":
    unittest.main()
