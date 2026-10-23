"""Sugar and maize come from where they grow and what a society knows, not from every opening (Complaint 560). Rome's opened
diet has no rule test (Complaint 560)."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.geography import crop_climate

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLD_WORLD = ("rome_100ad", "han_china_100ad", "england_1300", "norse_900ad")


def _entries():
    merged = {}
    production = os.path.join(ROOT, "data", "production")
    for name in sorted(os.listdir(production)):
        if name.endswith(".json") and not name.startswith("_"):
            with open(os.path.join(production, name), encoding="utf-8") as handle:
                merged.update(json.load(handle).get("materials") or {})
    return merged


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return json.load(handle)


class SugarAndMaizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = _entries()

    def test_sugar_cane_cannot_grow_in_a_temperate_or_cold_climate(self):
        sugar = self.entries["mat_sugar"]
        self.assertFalse(crop_climate.territory_suits(sugar, {"Csa", "Csb", "Cfb", "Dfb", "Dfc", "BSk", "ET"}))
        self.assertTrue(crop_climate.territory_suits(sugar, {"Aw"}))

    def test_maize_needs_a_node_no_old_world_start_holds(self):
        node = self.entries["maize_kg"]["requires_node"]
        self.assertTrue(node)
        for civilisation_id in OLD_WORLD:
            self.assertNotIn(node, _read("data", "civilizations", civilisation_id + ".json")["starting_techs"],
                             civilisation_id)
        self.assertIn(node, _read("data", "civilizations", "mexica_1500.json")["starting_techs"])


    def test_rendered_fat_serves_no_food_need(self):
        self.assertEqual(_read("data", "world", "needs.json")["goods"]["fat_kg"]["satisfies"], {})


if __name__ == "__main__":
    unittest.main()
