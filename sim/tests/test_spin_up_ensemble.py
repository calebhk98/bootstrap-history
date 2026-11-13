"""SCENARIO (Complaint 473): the spin-up is chaotic, so a rule change is judged on several replays that differ only by a
rounding-level perturbation of the households' cash, summarised as a distribution."""
QUICK_TOPIC = True

import unittest

from sim.markets.spin_up_ensemble import cash_factor, scaling_transfers, stage_trend, summarise_members
from sim.markets.spin_up_gap import SPIN_UP_RATE_FLOOR


class PerturbationTests(unittest.TestCase):
    def test_member_k_scales_cash_by_one_plus_k_times_the_step_and_member_zero_by_one(self):
        self.assertEqual(cash_factor(0), 1.0)
        self.assertEqual(cash_factor(3), 1.0 + 3 * 1e-12)

    def test_each_cohort_gains_the_factor_minus_one_of_its_cash_and_a_factor_of_one_posts_nothing(self):
        transfers = scaling_transfers({"a": 100.0, "b": 50.0}, "coin", 1.5)
        gains = {transfer.payee: transfer.amount for transfer in transfers}
        self.assertEqual(gains, {"a": 50.0, "b": 25.0})
        self.assertEqual(scaling_transfers({"a": 100.0}, "coin", 1.0), [])


class TrendTests(unittest.TestCase):
    def test_a_flat_series_has_no_trend(self):
        self.assertEqual(stage_trend([5.0, 5.0, 5.0, 5.0], 0.0, None), 0.0)

    def test_a_rising_series_gives_the_second_half_mean_minus_the_first_over_the_second(self):
        # halves {1, 3} and {3, 5}: means 2 and 4
        self.assertAlmostEqual(stage_trend([1.0, 3.0, 3.0, 5.0], 0.0, None), 0.5)

    def test_the_floor_replaces_a_second_half_mean_below_it(self):
        # means 0.0 and 0.002 against the rate floor
        self.assertAlmostEqual(stage_trend([0.0, 0.0, 0.002, 0.002], SPIN_UP_RATE_FLOOR, None), 0.002 / SPIN_UP_RATE_FLOOR)

    def test_a_supplied_base_replaces_the_second_half_mean_so_unmet_need_is_read_against_the_food_need(self):
        self.assertAlmostEqual(stage_trend([0.0, 0.0, 1.0, 1.0], 0.0, 10.0), 0.1)

    def test_a_series_with_nothing_measured_has_no_trend(self):
        self.assertIsNone(stage_trend([None, None], 0.0, None))


class SummaryTests(unittest.TestCase):
    def test_median_and_spread_are_taken_across_members_per_quantity(self):
        summary = summarise_members([{"rate": 0.1, "prices": 1.0}, {"rate": 0.4, "prices": 3.0},
                                     {"rate": 0.2, "prices": 2.0}, {"rate": 0.3, "prices": 10.0}])
        self.assertEqual(summary["rate"]["gaps"], [0.1, 0.4, 0.2, 0.3])
        self.assertAlmostEqual(summary["rate"]["median"], 0.25)
        self.assertAlmostEqual(summary["rate"]["spread"], 0.3)
        self.assertEqual(summary["prices"]["median"], 2.5)
        self.assertEqual(summary["prices"]["spread"], 9.0)


if __name__ == "__main__":
    unittest.main()
