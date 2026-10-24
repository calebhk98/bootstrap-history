"""Farm hours move toward what the farm is needed for, the rest of the hours are shared by trade, and a
wage that signals scarcity eases back once hours meet need; the training premium grows with the interest
rate (Complaint 640: the schedule built from a game's own rate is in test_labour_follows_need_scenario)."""
QUICK_TOPIC = True

import unittest

from sim.labour import labour_allocation
from sim.tests import harness  # noqa: F401  (the suite's shared setup)
from sim.labour import labour_market, wages

FARM = labour_allocation.FARM_TRADE
TOTAL_HOURS = 1000.0


class HoursFollowNeedTests(unittest.TestCase):

    def test_farm_hours_move_toward_need_within_the_mobility_limit(self):
        first = labour_allocation.farm_hours_after(500.0, 900.0, TOTAL_HOURS)
        self.assertGreater(first, 500.0)
        self.assertLess(first, 900.0)
        ceiling = labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR
        self.assertLessEqual(first - 500.0, ceiling * 500.0)

    def test_farm_hours_close_the_gap_over_years_without_overshooting(self):
        farm = 500.0
        series = []
        for _year in range(200):
            farm = labour_allocation.farm_hours_after(farm, 900.0, TOTAL_HOURS)
            series.append(farm)
        self.assertEqual(series, sorted(series))
        self.assertLessEqual(series[-1], 900.0 + 1e-9)
        self.assertGreater(series[-1], 899.0)

    def test_farm_hours_leave_the_farm_when_it_is_needed_less(self):
        self.assertLess(labour_allocation.farm_hours_after(500.0, 300.0, TOTAL_HOURS), 500.0)

    def test_the_rest_of_the_hours_are_shared_by_trade_and_nothing_is_lost(self):
        hours = labour_allocation.society_hours(TOTAL_HOURS, 600.0, {"smith": 0.25, "potter": 0.75})
        self.assertEqual(hours, {FARM: 600.0, "smith": 100.0, "potter": 300.0})
        self.assertAlmostEqual(sum(hours.values()), TOTAL_HOURS)

    def test_a_tightness_factor_rises_while_a_trade_is_short_and_eases_back_once_it_is_not(self):
        factor = 1.0
        for _year in range(20):
            factor = wages.adjusted_tightness_factor(factor, 300.0, 50.0)
        peak = factor
        self.assertGreater(peak, 1.0)
        for _year in range(400):
            factor = wages.adjusted_tightness_factor(factor, 300.0, 300.0)
        self.assertLess(factor, peak)

    def test_one_function_gives_the_need_to_allocation_and_wages(self):
        needed = labour_allocation.hours_needed_by_trade(
            {"smith": 0.25, "potter": 0.75}, 1000.0, 600.0)
        self.assertEqual(needed, {FARM: 600.0, "smith": 100.0, "potter": 300.0})


class TrainingPremiumTests(unittest.TestCase):

    def test_higher_interest_rate_gives_a_larger_premium(self):
        self.assertGreater(wages.training_premium(5.0, 0.30), wages.training_premium(5.0, 0.05))

    def test_the_default_constant_is_gone(self):
        self.assertFalse(hasattr(wages, "DEFAULT_DISCOUNT_RATE"))


if __name__ == "__main__":
    unittest.main()
