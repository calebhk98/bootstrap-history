"""price_step: a market's price moves to its clearing price, by no more than a year's limit either way."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy.price_step import PRICE_MOVE_LIMIT_PER_YEAR, within_a_years_move

LAST = 8.0
LIMIT = 0.25


class WithinAYearsMove(unittest.TestCase):
    def test_a_clearing_price_inside_the_band_is_the_years_price(self):
        self.assertEqual(within_a_years_move(9.0, LAST, LIMIT), 9.0)
        self.assertEqual(within_a_years_move(7.0, LAST, LIMIT), 7.0)

    def test_a_clearing_price_above_the_band_is_held_to_the_limit_above_last_years(self):
        self.assertAlmostEqual(within_a_years_move(800.0, LAST, LIMIT), LAST * (1.0 + LIMIT))

    def test_a_clearing_price_under_the_band_is_held_to_the_same_factor_under_last_years(self):
        self.assertAlmostEqual(within_a_years_move(0.008, LAST, LIMIT), LAST / (1.0 + LIMIT))

    def test_a_rise_and_a_fall_at_the_limit_undo_each_other(self):
        risen = within_a_years_move(math.inf, LAST, LIMIT)
        self.assertAlmostEqual(within_a_years_move(0.0, risen, LIMIT), LAST)

    def test_a_market_with_no_price_yet_takes_the_clearing_price(self):
        self.assertEqual(within_a_years_move(800.0, None, LIMIT), 800.0)
        self.assertEqual(within_a_years_move(800.0, math.nan, LIMIT), 800.0)
        self.assertEqual(within_a_years_move(800.0, 0.0, LIMIT), 800.0)

    def test_no_clearing_price_gives_none(self):
        self.assertIsNone(within_a_years_move(None, LAST, LIMIT))

    def test_the_limit_defaults_to_the_declared_one(self):
        self.assertAlmostEqual(within_a_years_move(800.0, LAST), LAST * (1.0 + PRICE_MOVE_LIMIT_PER_YEAR))


if __name__ == "__main__":
    unittest.main()
