"""Complaint 513: the food need's satiation is a sourced biological limit, and the hands kept on the land
follow the value of a farm hour against the wage."""

QUICK_TOPIC = True

import unittest

from sim.constants import REGISTRY
from sim.default_civilisation import REPOSITORY_ROOT
from sim.engine import need_data
from sim.labour import farm_intake
from sim.world import agriculture, demand


class SatiationDataTests(unittest.TestCase):
    def test_food_need_declares_a_satiation_level_equal_to_the_biological_limit(self):
        food = need_data.load_needs(REPOSITORY_ROOT)["needs"]["food"]
        limit = agriculture.MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE * demand.FOOD_SUBSISTENCE_QUANTITY_KG_PER_CAPITA_PER_YEAR
        self.assertAlmostEqual(food["satiation_per_capita_per_year"], limit, delta=0.005 * limit)

    def test_the_limit_is_declared_as_a_sourced_biological_parameter(self):
        entry = REGISTRY["MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE"]
        self.assertEqual(entry["kind"], "biological_parameter")
        self.assertTrue(entry["source"])
        self.assertGreater(entry["value"], 1.0)
        self.assertLess(entry["value"], 2.0)


class KeptFarmWorkersTests(unittest.TestCase):
    def test_hands_stay_while_a_farm_hour_pays_at_least_the_wage_and_food_is_still_wanted(self):
        self.assertEqual(farm_intake.kept_farm_workers(
            current_fte=80.0, satiation_fte=100.0, land_limit_fte=200.0, farm_hour_value_over_wage=3.0), 80.0)

    def test_hands_beyond_what_satiation_uses_do_not_stay(self):
        self.assertEqual(farm_intake.kept_farm_workers(
            current_fte=150.0, satiation_fte=100.0, land_limit_fte=200.0, farm_hour_value_over_wage=3.0), 100.0)

    def test_hands_beyond_the_land_do_not_stay(self):
        self.assertEqual(farm_intake.kept_farm_workers(
            current_fte=80.0, satiation_fte=100.0, land_limit_fte=60.0, farm_hour_value_over_wage=3.0), 60.0)

    def test_cheap_food_keeps_nobody(self):
        self.assertEqual(farm_intake.kept_farm_workers(
            current_fte=80.0, satiation_fte=100.0, land_limit_fte=200.0, farm_hour_value_over_wage=0.5), 0.0)

    def test_no_price_signal_keeps_nobody(self):
        self.assertEqual(farm_intake.kept_farm_workers(
            current_fte=80.0, satiation_fte=100.0, land_limit_fte=200.0, farm_hour_value_over_wage=None), 0.0)
