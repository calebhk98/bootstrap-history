"""Each shared helper or constant has one owner; the callers that differ in edge handling say so at the call."""

QUICK_TOPIC = True

import json
import os
import re
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


def sources():
    for folder, _directories, names in os.walk(SIM_DIR):
        if os.path.basename(folder) in ("tests", "__pycache__"):
            continue
        for name in names:
            if name.endswith(".py"):
                yield os.path.join(folder, name)


class OneDeclaration(unittest.TestCase):

    def assert_no_bare_assignment(self, pattern):
        owner = os.path.abspath(unit_conversions.__file__)
        found = []
        for path in sources():
            if os.path.abspath(path) == owner:
                continue
            with open(path, encoding="utf-8") as handle:
                for number, line in enumerate(handle, 1):
                    if re.match(pattern, line):
                        found.append("%s:%d" % (path, number))
        self.assertEqual([], found)

    def test_kilograms_per_tonne_is_declared_once(self):
        self.assert_no_bare_assignment(r"\s*KILOGRAMS_PER_TONNE\s*=\s*1000")

    def test_hours_per_person_year_is_declared_once(self):
        self.assert_no_bare_assignment(r"\s*HOURS_PER_(PERSON|WORKER)_YEAR\s*=\s*(declare|[0-9])")
        self.assertEqual(2000.0, unit_conversions.HOURS_PER_PERSON_YEAR)

    def test_no_module_restates_the_civil_year_in_days(self):
        self.assert_no_bare_assignment(r"\s*(CIVIL_)?DAYS_PER_YEAR\s*=\s*365\.0\s*$")
        self.assertEqual(365.0, unit_conversions.CIVIL_DAYS_PER_YEAR)

    def test_no_price_level_goes_by_the_bare_name(self):
        """The engine's level is `home_price_level`, the agent economy's index is `basket_price_level`, the
        balance of payments' is `money_stock_price_level`; a bare `price_level` would not say which."""
        found = []
        for path in sources():
            with open(path, encoding="utf-8") as handle:
                for number, line in enumerate(handle, 1):
                    if re.match(r"\s*def price_level\(", line):
                        found.append("%s:%d" % (path, number))
        self.assertEqual([], found)

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
        land_tiles = geography_api.load_geography()["land_tiles"]
        folder = os.path.join(DATA_DIR, "civilizations")
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(folder, name), encoding="utf-8") as handle:
                regions = json.load(handle).get("home_regions") or []
            self.assertEqual(geography_api.tiles_of_regions(regions),
                             land._tile_ids_for_home_regions(regions, land_tiles), name)


if __name__ == "__main__":
    unittest.main()
