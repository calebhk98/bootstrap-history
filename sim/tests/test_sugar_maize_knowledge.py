"""Sugar and maize come from where they grow and what a society knows, not from every opening (Complaint 560)."""

import json
import os
import unittest

from sim.economy import opening
from sim.engine.economy_port_setup import build_setup
from sim.geography import crop_climate
from sim.tests.harness import unopened_sim

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GRAINS = ("wheat_kg", "millet_kg", "flour_kg")
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

    def test_rome_opens_with_no_sugar_or_maize_and_eats_grain_first(self):
        setup = build_setup(unopened_sim(civ="rome_100ad"))
        self.assertNotIn("mat_sugar", setup.opening_prices)
        self.assertNotIn("maize_kg", setup.opening_prices)
        record, _areas, _carriage = opening.open_economy(setup)
        needs = _read("data", "world", "needs.json")["goods"]
        units = {good: record.opening_basket.get(good, 0.0) * attributes["satisfies"]["food"]
                 for good, attributes in needs.items() if "food" in attributes["satisfies"]}
        self.assertEqual(units["mat_sugar"], 0.0)
        self.assertEqual(units["maize_kg"], 0.0)
        total = sum(units.values())
        grains = sum(units.get(good, 0.0) for good in GRAINS)
        self.assertGreater(grains / total, 0.5, {good: round(value / total, 3) for good, value in units.items() if value})

    def test_rome_food_units_follow_a_pre_modern_diet_and_no_one_good_dominates(self):
        # Roman diet composition (Garnsey, Food and Society in Classical Antiquity, 1999): cereals were the large
        # majority of calories; oil and wine were secondary. Cereals here must be a majority, and no other single
        # food may exceed a third of the units. Rendered fat is not a food in the model (Complaint 532).
        needs = _read("data", "world", "needs.json")["goods"]
        self.assertEqual(needs["fat_kg"]["satisfies"], {})
        record, _areas, _carriage = opening.open_economy(build_setup(unopened_sim(civ="rome_100ad")))
        units = {good: record.opening_basket.get(good, 0.0) * attributes["satisfies"]["food"]
                 for good, attributes in needs.items() if "food" in attributes["satisfies"]}
        total = sum(units.values())
        shares = {good: value / total for good, value in units.items() if value}
        self.assertGreater(sum(shares.get(good, 0.0) for good in GRAINS), 0.5, shares)
        for good, share in shares.items():
            if good not in GRAINS:
                self.assertLess(share, 1 / 3, (good, shares))
        self.assertLess(max(shares.values()), 0.5, shares)

    def test_sugar_cane_figures_name_their_sources_and_confidence(self):
        sugar = self.entries["mat_sugar"]
        self.assertEqual(sugar["conf"], "D")
        self.assertIn("Galloway", sugar["yield_basis"])
        self.assertIn("Deerr", sugar["yield_basis"])


if __name__ == "__main__":
    unittest.main()
