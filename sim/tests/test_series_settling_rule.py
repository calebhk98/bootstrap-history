"""Complaint 554: `series_settling` (sim/economy/settling.py) judges a series by its trend, its monotone share and its
steps, on built series, so a failure names the statistic."""
QUICK_TOPIC = True

import math
import unittest

from sim.economy.settling import series_settling


class SeriesStatisticTests(unittest.TestCase):
    def test_a_constant_series_is_settled(self):
        item = series_settling("flat", [2.0] * 30, as_ratio=True)
        self.assertEqual(item.trend_per_year, 0.0)
        self.assertTrue(item.settled)

    def test_a_steady_climb_is_drift_with_a_trend_equal_to_its_log_growth(self):
        item = series_settling("climb", [math.exp(0.03 * year) for year in range(40)], as_ratio=True)
        self.assertAlmostEqual(item.trend_per_year, 0.03, places=9)
        self.assertEqual(item.monotone_share, 1.0)
        self.assertTrue(item.drifting)
        self.assertFalse(item.settled)

    def test_a_cycle_around_a_level_is_not_drift_but_a_large_swing_is_not_bounded(self):
        small = series_settling("cycle", [1.0 + 0.02 * (-1) ** year for year in range(40)], as_ratio=True)
        self.assertFalse(small.drifting)
        self.assertTrue(small.settled)
        large = series_settling("swing", [1.0 + 0.6 * (-1) ** year for year in range(40)], as_ratio=True)
        self.assertFalse(large.steps_bounded)

    def test_only_the_window_is_judged(self):
        values = [math.exp(0.2 * year) for year in range(20)] + [5.0] * 40
        self.assertTrue(series_settling("late", values, as_ratio=True).settled)

    def test_the_interest_rate_is_judged_by_differences(self):
        item = series_settling("rate", [0.05 + 0.005 * year for year in range(30)], as_ratio=False)
        self.assertAlmostEqual(item.trend_per_year, 0.005, places=9)
        self.assertTrue(item.drifting)


if __name__ == "__main__":
    unittest.main()
