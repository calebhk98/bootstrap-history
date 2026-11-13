"""bids_adding_demand: a market's demand counts each buyer's want once over the rounds."""

CIVILISATIONS = ()   # builds no game, so the runner warms no start for it
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


class BidsAddingDemandIsContinuousInWhatWasCounted(unittest.TestCase):
    def test_a_first_round_bid_of_dust_size_takes_dust_off_the_added_demand_not_the_whole_bid(self):
        first_round = [Bid("household", "grain", "area", "tile", 0.0, 1e-12, 1.0, 0.0, 1000.0, 0)]
        respend = Bid("household", "grain", "area", "tile", 0.0, 100.0, 1.0, 0.0, 100.0, 1)
        added = bids_adding_demand(first_round, [respend])
        self.assertEqual(len(added), 1)
        self.assertAlmostEqual(added[0].flexible_quantity, 100.0, delta=1e-9)

    def test_a_respend_bid_larger_than_the_first_round_bid_adds_only_the_difference(self):
        first_round = [_bid("household", 60.0)]
        added = bids_adding_demand(first_round, [Bid("household", "grain", "area", "tile", 0.0, 100.0, 1.0, 0.0, 1000.0, 1)])
        self.assertEqual(len(added), 1)
        self.assertAlmostEqual(added[0].flexible_quantity, 40.0, delta=1e-9)
        self.assertAlmostEqual(added[0].budget, 400.0, delta=1e-9)


if __name__ == "__main__":
    unittest.main()
