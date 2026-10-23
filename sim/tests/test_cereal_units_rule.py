"""The cereal units of a food basket: flour and bread count whole and a meal counts by the flour among its food. Arithmetic on
the needs and production data; no game."""

QUICK_TOPIC = True

import unittest

from .test_sugar_maize_knowledge_scenario import _read, cereal_units


class CerealUnitsTests(unittest.TestCase):
    def test_flour_and_bread_are_cereal_and_a_meal_is_cereal_by_its_flour(self):
        needs = _read("data", "world", "needs.json")["goods"]
        self.assertAlmostEqual(cereal_units({"flour_kg": 1.0, "bread_kg": 2.0}, needs), 3.0)
        flour_food = 300.0 * needs["flour_kg"]["satisfies"]["food"]
        vegetable_food = 200.0 * needs["vegetable_kg"]["satisfies"]["food"]
        self.assertAlmostEqual(cereal_units({"cooked_meal_kg": 1.0}, needs), flour_food / (flour_food + vegetable_food))
        self.assertEqual(cereal_units({"olive_oil_kg": 5.0}, needs), 0.0)
