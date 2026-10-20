"""Complaint 640 (from 553): the rules under the spin-up sensitivity measurement (`simulator.py spin-up-sensitivity`,
sim/economy/spin_up_sensitivity.py). The measurement answered its question (the cycle is the economy's, not the
shared yearly step's) and is not a pass or fail; what stays tested is that its statistics and variants do what they say."""
QUICK_TOPIC = True

import math
import unittest

from sim.economy import api as economy_api

sensitivity = economy_api.spin_up_sensitivity


class StatisticsTests(unittest.TestCase):
    def test_a_series_with_a_known_period_is_measured_as_that_period(self):
        series = [math.exp(0.01 * year + 0.2 * math.sin(2.0 * math.pi * year / 12.0)) for year in range(200)]
        found = sensitivity.statistics_of(series)
        self.assertAlmostEqual(found["period"], 12.0, delta=0.5)
        self.assertAlmostEqual(found["drift"], 0.01, delta=0.002)
        self.assertAlmostEqual(found["amplitude"], 0.2 / math.sqrt(2.0), delta=0.02)

    def test_a_flat_series_has_no_amplitude_and_no_period(self):
        found = sensitivity.statistics_of([2.0] * 50)
        self.assertEqual(found["amplitude"], 0.0)
        self.assertEqual(found["period"], 0.0)

    def test_a_two_year_alternation_flips_every_move(self):
        found = sensitivity.statistics_of([1.0 + 0.5 * (year % 2) for year in range(40)])
        self.assertEqual(found["flips"], 1.0)

    def test_the_first_years_can_be_left_out(self):
        series = [100.0 / (1 + year) for year in range(10)] + [1.0] * 40
        self.assertEqual(sensitivity.statistics_of(series, skip=10)["drift"], 0.0)


class VariantTests(unittest.TestCase):
    def test_scaled_speeds_change_the_constant_in_the_block_and_restore_it_after(self):
        name = "EXPANSION_SHARE_PER_YEAR"
        holders = sensitivity._holders(name)
        self.assertTrue(holders)
        with sensitivity.scaled_speeds((name,), 0.5):
            for module, value in holders:
                self.assertAlmostEqual(getattr(module, name), 0.5 * value)
        for module, value in holders:
            self.assertEqual(getattr(module, name), value)

    def test_a_scaled_speed_never_exceeds_the_whole_gap_closed_in_a_year(self):
        name = "EXPANSION_SHARE_PER_YEAR"
        with sensitivity.scaled_speeds((name,), 1000.0):
            for module, _value in sensitivity._holders(name):
                self.assertEqual(getattr(module, name), sensitivity.SPEED_CEILING)

    def test_every_speed_a_variant_scales_exists_in_a_loaded_module(self):
        for name in sensitivity.ALL_SPEEDS:
            self.assertTrue(sensitivity._holders(name), name)

    def test_the_per_producer_factor_is_fixed_by_seed_and_agent_and_within_its_spread(self):
        first = sensitivity.speed_factor_of("producer:a", 1, 0.5)
        self.assertEqual(first, sensitivity.speed_factor_of("producer:a", 1, 0.5))
        self.assertNotEqual(first, sensitivity.speed_factor_of("producer:a", 2, 0.5))
        for seed in range(20):
            self.assertTrue(0.5 <= sensitivity.speed_factor_of("producer:b", seed, 0.5) <= 1.5)


class TableTests(unittest.TestCase):
    def test_the_table_has_one_line_per_requested_variant_with_its_measured_period(self):
        def series_of(variant, years):
            period = {"baseline": 12.0, "wages x2": 6.0}[variant]
            prices = [math.exp(0.2 * math.sin(2.0 * math.pi * year / period)) for year in range(120)]
            return prices, prices

        lines = sensitivity.table(series_of, 120, 0, ["baseline", "wages x2"]).splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("baseline"))
        self.assertIn("period 12.00", lines[0])
        self.assertIn("period  6.00", lines[1])


if __name__ == "__main__":
    unittest.main()
