"""Demand below total stock at a common floor proves every higher trial fails."""

QUICK_TOPIC = True

import random
import unittest
from unittest import mock

from sim.economy import goods_market, unsold_search
from sim.tests.test_unsold_stock_search import AREA, COST, GOOD, View, buyer, game, offer


class FloorProofTests(unittest.TestCase):
    def clear(self, bids, offers):
        setup, record = game(*(each.seller for each in offers), workshops=2)
        return unsold_search.clear_with_search(setup, record, View(), bids, offers, offers,
                                               GOOD, AREA, "coin", 100.0)

    def test_excess_stock_at_a_common_floor_needs_no_trial_clearing(self):
        with mock.patch.object(goods_market, "sold_by_seller", wraps=goods_market.sold_by_seller) as trial:
            offers, result = self.clear([buyer(50.0, 4.0 * COST)], [offer("a", 100.0, 5.0 * COST)])
        self.assertEqual(offers[0].reservation_price, COST)
        self.assertEqual(result.quantity, 50.0)
        self.assertEqual(trial.call_count, 0)

    def test_certified_and_uncertified_search_are_bit_identical(self):
        generator = random.Random(82)
        for _case in range(160):
            offers = [offer(str(index), generator.uniform(1.0, 100.0), generator.uniform(1.1, 20.0) * COST)
                      for index in range(generator.randrange(1, 5))]
            bids = [buyer(generator.uniform(0.0, 500.0), generator.uniform(0.1, 10.0) * COST)]
            actual = self.clear(bids, offers)
            with mock.patch.object(unsold_search, "all_at_floor", return_value=False):
                expected = self.clear(bids, offers)
            self.assertEqual(actual, expected)

    def test_duplicate_seller_keys_cannot_use_the_total_stock_proof(self):
        offers = [offer("a", 100.0, 5.0 * COST), offer("a", 100.0, 5.0 * COST)]
        buyers = goods_market.Buyers([buyer(150.0, 4.0 * COST)], 100.0)
        self.assertFalse(unsold_search.all_at_floor(buyers, offers, {0: COST, 1: COST}))

    def test_different_floors_or_enough_demand_cannot_skip_the_search(self):
        offers = [offer("a", 100.0, 5.0 * COST), offer("b", 100.0, 5.0 * COST)]
        buyers = goods_market.Buyers([buyer(300.0, 4.0 * COST)], 100.0)
        self.assertFalse(unsold_search.all_at_floor(buyers, offers, {0: COST, 1: COST}))
        self.assertFalse(unsold_search.all_at_floor(buyers, offers, {0: COST, 1: COST / 2.0}))


if __name__ == "__main__":
    unittest.main()
