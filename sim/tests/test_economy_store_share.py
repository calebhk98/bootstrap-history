"""How much of savings households hold as goods."""
import unittest

from sim.economy.households_orders import HOUSEHOLD_TIME_PREFERENCE
from sim.economy.households_store import STORE_SAVINGS_SHARE, STORE_SHARE_LIMIT, store_value_target


class StoreShareTests(unittest.TestCase):
    def test_no_savings_gives_nothing(self):
        self.assertEqual(store_value_target(0.0, 0.1, 0.0), 0.0)
        self.assertEqual(store_value_target(-5.0, 0.1, 0.0), 0.0)

    def test_it_rises_with_expected_inflation(self):
        self.assertGreater(store_value_target(100.0, 0.05, 0.0), store_value_target(100.0, 0.0, 0.0))

    def test_it_is_capped(self):
        self.assertAlmostEqual(store_value_target(100.0, 1000.0, 0.0), 100.0 * STORE_SHARE_LIMIT)

    def test_it_falls_as_the_real_rate_rises(self):
        low = store_value_target(100.0, 0.0, HOUSEHOLD_TIME_PREFERENCE)
        high = store_value_target(100.0, 0.0, 4.0 * HOUSEHOLD_TIME_PREFERENCE)
        self.assertAlmostEqual(low, 100.0 * STORE_SAVINGS_SHARE)
        self.assertLess(high, low)


if __name__ == "__main__":
    unittest.main()
