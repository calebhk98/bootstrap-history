"""bids_adding_demand: a market's demand counts each buyer's want once over the rounds."""
import unittest

from sim.economy.goods_respend import bids_adding_demand
from sim.economy.types import Bid


def _bid(buyer, floor, priority=0):
    return Bid(buyer, "grain", "area", "tile", floor, 0.0, 1.0, 0.0, 1000.0, priority)


class BidsAddingDemandTests(unittest.TestCase):
    def test_a_buyer_that_asked_for_one_hundred_and_re_bids_forty_adds_nothing(self):
        first_round = [_bid("household", 100.0)]      # got 60 of the 100
        self.assertEqual(bids_adding_demand(first_round, [_bid("household", 40.0, 1)]), [])

    def test_a_buyer_new_to_the_market_counts_in_full(self):
        first_round = [_bid("household", 100.0)]
        respend = [_bid("household", 40.0, 1), _bid("neighbour", 30.0, 1)]
        self.assertEqual(bids_adding_demand(first_round, respend), [respend[1]])


if __name__ == "__main__":
    unittest.main()
