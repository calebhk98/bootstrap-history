"""Complaint 473: a good with standing bids and few or no sellers (a cart a merchant must replace, brick, a
by-product with no maker) does not have a remembered price that grows without bound: it stays within a multiple
of what the good costs to make, year after year, where trade is thin or none."""

QUICK_TOPIC = True

import unittest

from sim.economy.market_memory_asks import price_after_resumed_trade
from sim.economy.market_memory_offers import (PRICE_OVER_MAKING_COST_LIMIT, price_after_no_offers,
                                              price_within_making_cost)


class PriceWithinMakingCostTests(unittest.TestCase):
    def test_a_price_far_above_cost_is_held_to_the_limit(self):
        self.assertEqual(price_within_making_cost(1e8, 100.0), PRICE_OVER_MAKING_COST_LIMIT * 100.0)

    def test_a_price_within_the_limit_is_untouched(self):
        self.assertEqual(price_within_making_cost(150.0, 100.0), 150.0)

    def test_a_good_nobody_can_make_has_no_cost_to_cap_it(self):
        self.assertEqual(price_within_making_cost(1e8, None), 1e8)

    def test_bids_without_sellers_stay_at_or_under_the_limit_year_after_year(self):
        cost, price = 100.0, 100.0
        for _year in range(40):
            clearing_price = price * 3.0                  # a tiny trade priced by scarcity, each year dearer
            signal = price_after_resumed_trade(price, clearing_price, 0)
            signal = price_after_no_offers(signal, cost) or signal
            price = price_within_making_cost(max(signal, clearing_price), cost)
            self.assertLessEqual(price, PRICE_OVER_MAKING_COST_LIMIT * cost)


if __name__ == "__main__":
    unittest.main()
