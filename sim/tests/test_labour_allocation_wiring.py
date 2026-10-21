"""The rules that size the farm's hours every simulated year (Complaint 640: called on inputs built here; the
whole-game checks that the year's allocation responds to food scarcity are in
test_labour_allocation_wiring_scenario)."""
QUICK_TOPIC = True

import unittest

from .harness import *  # noqa: F401,F403
from sim.labour import labour_allocation

FARM = labour_allocation.FARM_TRADE


class FarmWorkersNeededTests(unittest.TestCase):

    def test_land_saturation_caps_the_farm_need(self):
        # Workers beyond what the land can employ produce nothing more.
        need = labour_allocation.farm_workers_needed(
            baseline_fte=100.0, current_fte=100.0, shortfall_kg=1e12,
            marginal_product_kg_per_hour=0.001, land_hectares=210.0)
        self.assertLessEqual(need, 210.0 / labour_allocation.agriculture.hectares_cropped_per_farm_worker() + 1e-9)

    def test_no_shortfall_and_no_surplus_keeps_the_baseline(self):
        self.assertEqual(labour_allocation.farm_workers_needed(100.0, 100.0, 0.0, 0.5, 1e6), 100.0)

    def test_a_shortfall_calls_for_more_hands(self):
        self.assertGreater(labour_allocation.farm_workers_needed(100.0, 100.0, 5e5, 5.0, 1e6), 100.0)

    def test_a_surplus_lets_hands_go(self):
        self.assertLess(labour_allocation.farm_workers_needed(100.0, 100.0, 0.0, 5.0, 1e6, surplus_kg=1e5), 100.0)

    def test_a_bigger_shortfall_calls_for_no_fewer_hands(self):
        small = labour_allocation.farm_workers_needed(100.0, 100.0, 1e5, 5.0, 1e6)
        large = labour_allocation.farm_workers_needed(100.0, 100.0, 5e5, 5.0, 1e6)
        self.assertGreaterEqual(large, small)


class FarmHoursMoveTests(unittest.TestCase):

    def test_hours_move_toward_what_the_farm_is_needed_for(self):
        total = 1.0e6
        self.assertGreater(labour_allocation.farm_hours_after(1000.0, 5000.0, total), 1000.0)
        self.assertLess(labour_allocation.farm_hours_after(5000.0, 1000.0, total), 5000.0)

    def test_hours_at_the_need_stay_there(self):
        self.assertEqual(labour_allocation.farm_hours_after(1000.0, 1000.0, 1.0e6), 1000.0)

    def test_hours_move_no_further_than_the_gap(self):
        after = labour_allocation.farm_hours_after(1000.0, 1010.0, 1.0e6)
        self.assertLessEqual(after, 1010.0)

    def test_hours_never_exceed_all_the_hours_or_go_below_zero(self):
        self.assertLessEqual(labour_allocation.farm_hours_after(1000.0, 1.0e9, 2000.0), 2000.0)
        self.assertGreaterEqual(labour_allocation.farm_hours_after(1000.0, 0.0, 2000.0), 0.0)

    def test_the_year_starts_from_the_held_split_scaled_to_this_years_hours(self):
        held = {FARM: 300.0, "smith": 100.0}
        self.assertAlmostEqual(labour_allocation.current_farm_hours(held, 2000.0, 10.0), 1500.0)

    def test_the_opening_year_starts_from_the_food_balance_never_above_all_the_hours(self):
        hours_per_worker = labour_allocation.HOURS_PER_FARM_WORKER_YEAR
        self.assertEqual(labour_allocation.current_farm_hours({}, 1.0e9, 10.0), 10.0 * hours_per_worker)
        self.assertEqual(labour_allocation.current_farm_hours({}, 100.0, 10.0), 100.0)


if __name__ == "__main__":
    unittest.main()
