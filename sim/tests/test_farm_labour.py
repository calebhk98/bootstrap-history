"""The labour of a wheat hectare is built from sub-tasks (data/world/farm_labour.json), not typed.

Each test calls the rule in sim/world/farm_labour.py on inputs built here, then checks that the recipes and the
declared constants follow it."""
import json
import os
import unittest

from sim.unit_conversions import HOURS_PER_PERSON_YEAR, WORKING_DAYS_PER_YEAR
from sim.world import agriculture, farm_labour

QUICK_TOPIC = True

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def built_data(cycle_days, reaping_days, threshing_share, by_hand_hours, with_oxen_hours):
    return {"wheat": {
        "tasks": {"cultivation_cycle": {"person_days": cycle_days},
                  "reaping": {"person_days": reaping_days},
                  "threshing": {"person_days_as_share_of_reaping": threshing_share}},
        "hand_tilling": {"hours_per_hectare_by_hand_tools": by_hand_hours,
                         "hours_per_hectare_with_oxen": with_oxen_hours}}}


class FarmLabourRuleTests(unittest.TestCase):
    def test_hours_are_the_sum_of_the_sub_task_person_days_at_the_working_day(self):
        data = built_data(40.0, 6.0, 1.0, 400.0, 60.0)
        self.assertEqual(farm_labour.wheat_task_person_days(data),
                         {"cultivation_cycle": 40.0, "reaping": 6.0, "threshing": 6.0})
        self.assertAlmostEqual(farm_labour.wheat_hours_per_hectare(data, 8.0), (40.0 + 6.0 + 6.0) * 8.0)

    def test_threshing_follows_the_reaping_by_its_share(self):
        data = built_data(40.0, 6.0, 0.5, 400.0, 60.0)
        self.assertAlmostEqual(farm_labour.wheat_task_person_days(data)["threshing"], 3.0)

    def test_hand_tilling_adds_the_difference_to_the_oxen_tilling(self):
        data = built_data(40.0, 6.0, 1.0, 400.0, 60.0)
        self.assertAlmostEqual(farm_labour.wheat_hand_tilling_extra_hours(data), 340.0)
        self.assertAlmostEqual(farm_labour.wheat_hoe_hours_per_hectare(data, 10.0),
                               farm_labour.wheat_hours_per_hectare(data, 10.0) + 340.0)

    def test_reaping_rate_is_the_inverse_of_the_reaping_sub_task(self):
        data = built_data(40.0, 8.0, 1.0, 400.0, 60.0)
        self.assertAlmostEqual(farm_labour.wheat_reaping_hectares_per_person_day(data), 0.125)

    def test_the_working_day_is_the_models_year_over_its_working_days(self):
        self.assertAlmostEqual(farm_labour.hours_per_working_day(), HOURS_PER_PERSON_YEAR / WORKING_DAYS_PER_YEAR)


class FarmLabourFollowedByTheModelTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "data", "production", "40_organics.json"), encoding="utf-8") as handle:
            self.recipes = json.load(handle)["materials"]

    def test_the_recipes_book_the_sub_task_hours(self):
        data = farm_labour.load_farm_labour()
        day = farm_labour.hours_per_working_day()
        self.assertAlmostEqual(self.recipes["wheat_kg"]["labour_hours"]["farmer"],
                               farm_labour.wheat_hours_per_hectare(data, day))
        self.assertAlmostEqual(self.recipes["wheat_hoe_kg"]["labour_hours"]["farmer"],
                               farm_labour.wheat_hoe_hours_per_hectare(data, day))

    def test_the_farm_year_model_reads_the_same_hours_and_reaping_rate(self):
        self.assertEqual(farm_labour.REFERENCE_LABOUR_HOURS_PER_HECTARE, farm_labour.WHEAT_HOURS_PER_HECTARE)
        self.assertEqual(agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE, farm_labour.WHEAT_HOURS_PER_HECTARE)
        self.assertEqual(agriculture.HECTARES_REAPED_PER_WORKER_DAY, farm_labour.WHEAT_REAPED_HECTARES_PER_PERSON_DAY)
        self.assertEqual(agriculture.HARVEST_WORKING_DAY_HOURS, farm_labour.hours_per_working_day())

    def test_every_sub_task_in_the_data_quotes_its_source(self):
        for name, task in farm_labour.load_farm_labour()["wheat"]["tasks"].items():
            self.assertTrue(task["quote"].strip(), name)


if __name__ == "__main__":
    unittest.main()
