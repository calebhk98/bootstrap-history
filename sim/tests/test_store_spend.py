"""What a household spends on its store of durable goods in a year: the wear it replaces, and a shortfall it closes."""

QUICK_TOPIC = True

import unittest

from sim.economy import durable_stock
from sim.economy.store_spend import STORE_GAP_CLOSING, store_spend
from sim.economy.types import GoodSpec

BAND = 0.2


class StoreSpendTests(unittest.TestCase):
    def test_wear_inside_the_band_is_replaced(self):
        # holds 95 of 100 wanted; a tenth of the stock wears out a year, so the 5 short is bought back
        self.assertAlmostEqual(store_spend(100.0, 95.0, 0.1, 1000.0, BAND), 5.0)

    def test_inside_the_band_no_more_than_a_years_wear_is_bought(self):
        # holds 85 of 100 wanted: inside the band, so the 15 short is bought back at the pace of wear, 5 a year
        self.assertAlmostEqual(store_spend(100.0, 85.0, 0.05, 1000.0, BAND), 5.0)

    def test_nothing_is_bought_at_or_above_the_wanted_value(self):
        self.assertEqual(store_spend(100.0, 100.0, 0.1, 1000.0, BAND), 0.0)
        self.assertEqual(store_spend(100.0, 130.0, 0.1, 1000.0, BAND), 0.0)

    def test_a_shortfall_beyond_the_band_is_closed_over_years_not_at_once(self):
        # holds 50 of 100 wanted: a share of the 50 short is bought, so a one-year swing in the target is not a one-year purchase
        self.assertAlmostEqual(store_spend(100.0, 50.0, 0.01, 1000.0, BAND), STORE_GAP_CLOSING * 50.0)

    def test_a_shortfall_beyond_the_band_is_bought_at_least_at_the_pace_of_wear(self):
        self.assertAlmostEqual(store_spend(100.0, 50.0, 0.9, 1000.0, BAND), 50.0)
        self.assertAlmostEqual(store_spend(100.0, 70.0, 0.5, 1000.0, BAND), 30.0)

    def test_spending_never_exceeds_the_pot(self):
        self.assertAlmostEqual(store_spend(100.0, 10.0, 0.1, 20.0, BAND), 20.0)
        self.assertAlmostEqual(store_spend(100.0, 95.0, 0.1, 2.0, BAND), 2.0)

    def test_a_stock_that_does_not_wear_is_bought_only_beyond_the_band(self):
        self.assertEqual(store_spend(100.0, 90.0, 0.0, 1000.0, BAND), 0.0)

    def test_wear_share_is_one_over_the_service_life(self):
        self.assertAlmostEqual(durable_stock.wear_share(GoodSpec("tool", 1.0, 0.0, 4.0, "tool")), 0.25)
        self.assertEqual(durable_stock.wear_share(GoodSpec("tool", 1.0, 0.0, 0.5, "tool")), 1.0)
        self.assertEqual(durable_stock.wear_share(GoodSpec("tool", 1.0, 0.0, 0.0, "tool")), 0.0)


if __name__ == "__main__":
    unittest.main()
