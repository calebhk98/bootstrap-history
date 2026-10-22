"""Complaint 526: the weights of the observed-inflation median are what the goods traded for the year before (volume
times price), not the opening basket's quantities at base prices: an opening quantity a market never realises (a good
whose opening price is a cost estimate and which barely trades) must not decide what the economy's prices did."""

QUICK_TOPIC = True

import unittest

from sim.economy import currency
from sim.economy.national_prices import traded_spending_weights


class TradedSpendingWeightTests(unittest.TestCase):
    def test_a_weight_is_the_goods_volume_over_its_areas_times_last_years_price(self):
        weights = traded_spending_weights({"bread|a": 10.0, "bread|b": 5.0, "salt|a": 2.0},
                                          {"bread": 2.0, "salt": 3.0}, {"bread", "salt"})
        self.assertEqual(weights, {"bread": 30.0, "salt": 6.0})

    def test_only_the_wanted_goods_count_and_a_good_with_no_price_or_volume_is_left_out(self):
        weights = traded_spending_weights({"bread|a": 10.0, "tin|a": 4.0, "salt|a": 0.0},
                                          {"bread": 2.0, "tin": 1.0, "salt": 3.0}, {"bread", "salt", "cloth"})
        self.assertEqual(weights, {"bread": 20.0})

    def test_a_good_that_dominates_the_opening_basket_but_barely_trades_does_not_set_the_inflation(self):
        before = {"glass": 1.0, "bread": 1.0, "flour": 1.0}
        now = {"glass": 1.0, "bread": 3.0, "flour": 3.0}
        opening = {"glass": 100.0, "bread": 1.0, "flour": 1.0}      # glass: nearly all of the opening basket's value
        traded = {"glass|a": 0.1, "bread|a": 50.0, "flour|a": 50.0}
        self.assertEqual(currency.price_inflation(now, before, opening), 0.0)
        weights = traded_spending_weights(traded, before, set(before))
        self.assertAlmostEqual(currency.price_inflation(now, before, weights), 2.0)


if __name__ == "__main__":
    unittest.main()
