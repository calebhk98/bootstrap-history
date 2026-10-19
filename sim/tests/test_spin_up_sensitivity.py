"""Complaint 553: is the spin-up's cycle the economy's, or the yearly step with every producer adjusting at once?

Runs the small fixture's quiet spin-up (fixed people and technology, no shocks) under variants of how the
economy adjusts (spin_up_sensitivity_support.VARIANTS) and compares the price level's and the wage's drift,
cycle amplitude and cycle period. The finding the assertions record: no variant removes the cycle, and the
amplitude moves by well under a factor of two, so the cycle is not a product of the shared step alone; the
period does move with the speeds. The Rome opening takes minutes a variant: its command is in
Complaints/553.
"""
import unittest

from sim.tests import spin_up_sensitivity_support as support

YEARS = 250
TRANSIENT_YEARS = 60            # the opening's fall to its first level is not the cycle
AMPLITUDE_RATIO_LIMIT = 2.0     # a variant's amplitude against the baseline's, either way
PERIOD_CHANGE_SHARE = 0.2       # the period moves by more than this under some speed change
_STATISTICS = {}


def statistics():
    if not _STATISTICS:
        for variant in support.VARIANTS:
            prices, wages = support.fixture_series(variant, YEARS)
            _STATISTICS[variant] = {"price": support.statistics_of(prices, TRANSIENT_YEARS),
                                    "wage": support.statistics_of(wages, TRANSIENT_YEARS)}
    return _STATISTICS


class SpinUpSensitivityTests(unittest.TestCase):
    def test_every_variant_has_a_drift_an_amplitude_and_a_period(self):
        for variant, by_series in statistics().items():
            for series, found in by_series.items():
                for key in ("drift", "amplitude", "period", "flips"):
                    self.assertIn(key, found, (variant, series))
                    self.assertEqual(found[key], found[key], (variant, series, key))       # not NaN

    def test_the_baseline_cycles_around_a_drift(self):
        baseline = statistics()["baseline"]["price"]
        self.assertGreater(baseline["amplitude"], 0.1)
        self.assertGreater(baseline["period"], 5.0)
        self.assertGreater(baseline["drift"], 0.0)

    def test_no_change_of_adjustment_speed_removes_the_cycle(self):
        baseline = statistics()["baseline"]["price"]["amplitude"]
        for variant, by_series in statistics().items():
            amplitude = by_series["price"]["amplitude"]
            self.assertGreater(amplitude, baseline / AMPLITUDE_RATIO_LIMIT, variant)
            self.assertLess(amplitude, baseline * AMPLITUDE_RATIO_LIMIT, variant)

    def test_the_period_follows_the_speeds(self):
        table = statistics()
        baseline = table["baseline"]["price"]["period"]
        scaled = [table[variant]["price"]["period"] for variant in table if " x" in variant]
        self.assertGreater(max(abs(period - baseline) / baseline for period in scaled), PERIOD_CHANGE_SHARE)

    def test_producers_with_their_own_speeds_still_cycle(self):
        table = statistics()
        baseline = table["baseline"]["price"]["amplitude"]
        for variant in ("per-producer speed seed 1", "per-producer speed seed 2"):
            self.assertGreater(table[variant]["price"]["amplitude"], 0.5 * baseline, variant)

    def test_a_series_with_a_known_period_is_measured_as_that_period(self):
        import math
        series = [math.exp(0.01 * year + 0.2 * math.sin(2.0 * math.pi * year / 12.0)) for year in range(200)]
        found = support.statistics_of(series)
        self.assertAlmostEqual(found["period"], 12.0, delta=0.5)
        self.assertAlmostEqual(found["drift"], 0.01, delta=0.002)
        self.assertAlmostEqual(found["amplitude"], 0.2 / math.sqrt(2.0), delta=0.02)


if __name__ == "__main__":
    unittest.main()
