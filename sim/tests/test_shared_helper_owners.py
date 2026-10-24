"""Shared helpers and constants: their values, and that callers agree with the owner."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim import json_files, unit_conversions
from sim.economy import unit_cost
from sim.economy.types import Recipe
from sim.geography import api as geography_api
from sim.world import capital_market, land

SIM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(SIM_DIR), "data")


def recipe_with_plant(plant_life_years):
    return Recipe("run", {"good": 1.0}, {}, {}, plant_goods={"pan": 3.0}, plant_life_years=plant_life_years)


class OneDeclaration(unittest.TestCase):

    def test_the_shared_unit_constants_have_their_values(self):
        self.assertEqual(1000.0, unit_conversions.KILOGRAMS_PER_TONNE)
        self.assertEqual(2000.0, unit_conversions.HOURS_PER_PERSON_YEAR)
        self.assertEqual(365.0, unit_conversions.CIVIL_DAYS_PER_YEAR)

    def test_json_files_are_listed_in_name_order_and_only_json(self):
        folder = os.path.join(DATA_DIR, "world")
        listed = json_files.json_files(folder)
        self.assertTrue(listed)
        self.assertEqual(sorted(listed), listed)
        self.assertTrue(all(path.endswith(".json") for path in listed))
        self.assertEqual([], json_files.json_files(os.path.join(folder, "no_such_folder")))


class CapitalRecoveryFactor(unittest.TestCase):

    def test_economy_charge_uses_the_world_factor_for_a_plant_with_a_life(self):
        for rate in (-0.1, 0.0, 0.05):
            self.assertEqual(
                3.0 * capital_market.capital_recovery_factor(rate, 20.0),
                unit_cost.capital_charge_per_run(recipe_with_plant(20.0), {"pan": 1.0}, {}, rate))

    def test_a_plant_with_no_life_is_repaid_within_the_run_and_the_world_factor_refuses_it(self):
        for rate in (0.0, 0.05):
            self.assertEqual(3.0, unit_cost.capital_charge_per_run(recipe_with_plant(0.0), {"pan": 1.0}, {}, rate))
        with self.assertRaises(ValueError):
            capital_market.capital_recovery_factor(0.05, 0.0)


class TilesOfACivilisation(unittest.TestCase):

    def test_land_and_geography_agree_on_the_tiles_of_every_civilisation(self):
        folder = os.path.join(DATA_DIR, "civilizations")
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(folder, name), encoding="utf-8") as handle:
                civilisation = json.load(handle)
            parcels = land.cultivable_land_for_civilization(name, civilizations={name: civilisation})
            self.assertEqual(len(parcels), len(geography_api.tiles_held(civilisation)), name)


if __name__ == "__main__":
    unittest.main()
