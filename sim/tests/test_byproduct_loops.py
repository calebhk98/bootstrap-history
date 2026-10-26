"""Complaints/544: straw, bran, dung, urine and nightsoil are made, bought and (if nobody buys) tipped.

Straw comes with grain, bran with milling, dung with herds and with the rearing of draught animals; urine and
nightsoil are collected from the town. Each has a consumer: fodder for animals, dung for the nitre bed, urine
for fulling and tanning, nightsoil for market gardens. What nobody bought is tipped at a recorded heap.
"""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.prices import disposal_cost
from sim.world import demand

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BYPRODUCTS = ("straw_kg", "bran_kg", "manure_kg", "urine_kg", "nightsoil_kg")
GRAIN_RECIPES = {"wheat_kg": "wheat_kg", "wheat_hoe_kg": "wheat_kg", "millet_kg": "millet_kg", "maize_kg": "maize_kg"}
MILLING_RECIPES = {"flour_kg": "wheat_kg", "flour_kg_millet": "millet_kg", "flour_kg_maize": "maize_kg"}
HERDS = {"wool_kg": "sheep_kg", "milk_kg": "goat_kg", "meat_kg": "cattle_kg"}
HERD_HEAD = 100.0


def read_json(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return json.load(handle)


class ByproductsAreJointOutputs(unittest.TestCase):

    def setUp(self):
        self.production = demand.production_data()
        self.stock = read_json("data", "world", "living_stock.json")["materials"]

    def test_straw_comes_with_the_grain_of_every_grain_recipe(self):
        for key, grain in GRAIN_RECIPES.items():
            outputs = self.production[key]["outputs"]
            self.assertGreater(outputs["straw_kg"], outputs[grain], key)  # stalk outweighs grain before the sickle
            self.assertLess(outputs["straw_kg"], 4.0 * outputs[grain], key)

    def test_bran_comes_with_the_flour_of_every_milling_recipe_and_mass_balances(self):
        for key, grain in MILLING_RECIPES.items():
            entry = self.production[key]
            self.assertGreater(entry["outputs"]["bran_kg"], 0.0, key)
            made = entry["outputs"]["flour_kg"] + entry["outputs"]["bran_kg"]
            self.assertLessEqual(made, entry["inputs"][grain], key)
            self.assertGreater(made, 0.9 * entry["inputs"][grain], key)  # only dust and moisture are lost

    def test_dung_and_fodder_of_each_herd_follow_the_species_row(self):
        for key, species in HERDS.items():
            row, entry = self.stock[species], self.production[key]
            weight = HERD_HEAD * row["live_weight_kg_per_head"]
            self.assertAlmostEqual(
                entry["outputs"]["manure_kg"],
                weight * row["manure_share_of_live_weight_per_day"] * 365.0 * row["manure_collected_share"], places=2)
            self.assertAlmostEqual(
                entry["inputs"]["straw_kg"],
                weight * row["fodder_dry_matter_share_of_live_weight_per_day"] * row["winter_fodder_days"]
                * row["straw_share_of_winter_ration"] / row["straw_dry_matter_share"], places=2)
            self.assertAlmostEqual(entry["inputs"].get("bran_kg", 0.0), HERD_HEAD * row["bran_kg_per_head_year"],
                                   places=2)

    def test_draught_animals_drop_dung_and_eat_straw_and_bran(self):
        entry = self.production["draught_animal_kg"]
        self.assertGreater(entry["outputs"]["manure_kg"], 0.0)
        self.assertGreater(entry["inputs"]["straw_kg"], 0.0)
        self.assertGreater(entry["inputs"]["bran_kg"], 0.0)

    def test_no_recipe_collects_dung_alone(self):
        for key, entry in self.production.items():
            if "manure_kg" in entry["outputs"]:
                self.assertGreater(len(entry["outputs"]), 1, key)

    def test_town_excreta_are_collected_per_person_year_with_a_source(self):
        for key in ("urine_kg", "nightsoil_kg"):
            entry = self.production[key]
            self.assertGreater(entry["excreted_kg_per_person_year"], 0.0, key)
            self.assertGreater(entry["labour_hours"]["labourer"], 0.0, key)
            self.assertIn(entry["conf"], ("A", "B", "C", "D"), key)
            self.assertGreater(len(entry["yield_basis"]), 100, key)


class EveryByproductHasAConsumerOrAHeap(unittest.TestCase):

    def setUp(self):
        self.production = demand.production_data()

    def consumers(self, material):
        return sorted(key for key, entry in self.production.items() if material in (entry.get("inputs") or {}))

    def makers(self, material):
        return sorted(key for key, entry in self.production.items() if material in entry["outputs"])

    def test_every_byproduct_is_made_by_some_recipe(self):
        for material in BYPRODUCTS:
            self.assertTrue(self.makers(material), material)

    def test_every_byproduct_has_a_recipe_that_consumes_it(self):
        for material in BYPRODUCTS:
            self.assertTrue(self.consumers(material), material)

    def test_the_named_consumers(self):
        self.assertIn("nitre_kg", self.consumers("manure_kg"))
        self.assertIn("cloth_kg", self.consumers("urine_kg"))  # fulling
        self.assertIn("leather_kg", self.consumers("urine_kg"))  # tanning
        self.assertTrue(self.consumers("nightsoil_kg"))  # market gardens
        for herd in ("wool_kg", "milk_kg", "meat_kg", "draught_animal_kg"):
            self.assertIn(herd, self.consumers("straw_kg"))
        self.assertIn("draught_animal_kg", self.consumers("bran_kg"))

    def test_the_market_garden_feeds_people(self):
        goods = read_json("data", "world", "needs.json")["goods"]
        gardens = [key for key in self.consumers("nightsoil_kg")]
        fed = [key for key in gardens if goods.get(key, {}).get("satisfies", {}).get("food", 0.0) > 0.0
               or self.production[key].get("satisfies", {}).get("food", 0.0) > 0.0]
        self.assertTrue(fed)

    def test_what_nobody_need_buy_has_a_heap_to_be_tipped_on(self):
        for material in BYPRODUCTS:
            self.assertIn(material, disposal_cost.waste_materials(), material)

    def test_the_standalone_dung_extraction_is_gone(self):
        self.assertNotIn("manure_kg", self.production)

    def test_no_byproduct_is_an_orphan_input(self):
        made = {material for entry in self.production.values() for material in entry["outputs"]}
        for key, entry in self.production.items():
            for material in (entry.get("inputs") or {}):
                if material in BYPRODUCTS:
                    self.assertIn(material, made, key)


if __name__ == "__main__":
    unittest.main()
