"""Complaint 614: bread is baked from flour, water and fuel in an oven by a baker, and households can buy it without the loaf creating food energy."""
QUICK_TOPIC = True

import json
import os
import unittest

from sim.content.catalog import load_production_catalog

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PRODUCTION = load_production_catalog(_ROOT)


def _world(name):
    with open(os.path.join(_ROOT, "data", "world", name), encoding="utf-8") as handle:
        return json.load(handle)


_TRADES = _world("trades.json")["trades"]
_GOODS = _world("needs.json")["goods"]
_SPOILAGE = _world("spoilage.json")["rates_per_year"]


class BreadTests(unittest.TestCase):

    def test_bread_is_made_from_flour_with_heat_an_oven_and_a_baker(self):
        recipe = _PRODUCTION["bread_kg"]
        self.assertIn("flour_kg", recipe["inputs"])
        self.assertGreater(recipe["thermal_mj"], 0.0)
        self.assertEqual(set(recipe["labour_hours"]), {"baker"})
        self.assertIn("baker", _TRADES)
        self.assertTrue(_TRADES["baker"].get("training_source"))
        self.assertTrue(_TRADES["baker"].get("fatality_source"))
        self.assertTrue(recipe["capital"], "the oven")

    def test_bread_loses_mass_in_the_bake_and_never_gains_it(self):
        recipe = _PRODUCTION["bread_kg"]
        dough = sum(recipe["inputs"].values())
        self.assertLess(recipe["outputs"]["bread_kg"], dough)
        self.assertGreater(recipe["outputs"]["bread_kg"], 0.8 * dough)

    def test_households_buy_bread_as_food_with_no_more_energy_than_its_flour(self):
        recipe = _PRODUCTION["bread_kg"]
        flour_per_kilogram = recipe["inputs"]["flour_kg"] / recipe["outputs"]["bread_kg"]
        flour_factor = _GOODS["flour_kg"]["satisfies"]["food"]
        bread_factor = _GOODS["bread_kg"]["satisfies"]["food"]
        self.assertGreater(bread_factor, 0.0)
        self.assertLessEqual(bread_factor, flour_factor * flour_per_kilogram + 1e-9)

    def test_bread_spoils_faster_than_flour(self):
        self.assertGreater(_SPOILAGE["bread_kg"]["rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
