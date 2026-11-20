"""plant_coin.coin_left_for_runs: the coin a producer has for the year's runs once the plant it rebuilds is paid for."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy.plant_coin import coin_left_for_runs


class CoinLeftForRuns(unittest.TestCase):
    def test_the_plant_to_rebuild_comes_off_the_coin_held(self):
        self.assertAlmostEqual(coin_left_for_runs(1000.0, 20.0, 12.0), 1000.0 - 20.0 * 12.0)

    def test_plant_that_costs_more_than_the_coin_held_leaves_nothing(self):
        self.assertEqual(coin_left_for_runs(100.0, 20.0, 12.0), 0.0)

    def test_no_plant_to_rebuild_leaves_all_the_coin(self):
        self.assertEqual(coin_left_for_runs(1000.0, 0.0, 12.0), 1000.0)

    def test_plant_whose_cost_cannot_be_worked_out_leaves_all_the_coin(self):
        for value in (math.nan, math.inf, 0.0, -5.0):
            self.assertEqual(coin_left_for_runs(1000.0, 20.0, value), 1000.0)

    def test_a_debit_is_no_coin(self):
        self.assertEqual(coin_left_for_runs(-50.0, 0.0, 12.0), 0.0)
        self.assertEqual(coin_left_for_runs(-50.0, 20.0, 12.0), 0.0)


if __name__ == "__main__":
    unittest.main()
