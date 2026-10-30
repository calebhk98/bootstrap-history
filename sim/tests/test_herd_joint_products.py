"""Complaints/532: wool, milk, meat, hides, tallow and horn come from a herd together, per animal-year.

The herd parameters (head per hectare, fleece, offtake, live weight, dressing, salt lick) sit in the
living-stock row of the species; each herd recipe is a batch of `HERD_HEAD` head-years and must follow
from that row. A society without the animal holds no gate node for its herd, so it cannot make the products.
"""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.engine import civ_start_check as start_check
from sim.content.catalog import load_production_catalog
from sim.content.tree_source import load_base_tree
from sim.world import demand

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERD_HEAD = 100.0
HERD_PRODUCTS = ("wool_kg", "milk_kg", "meat_kg", "hide_kg", "fat_kg", "horn_kg")
# herd recipe -> (species stock material, products it must make together)
HERDS = {
    "wool_kg": ("sheep_kg", ("wool_kg", "meat_kg", "hide_kg", "fat_kg")),
    "milk_kg": ("goat_kg", ("milk_kg", "meat_kg", "hide_kg", "fat_kg", "horn_kg")),
    "meat_kg": ("cattle_kg", ("milk_kg", "meat_kg", "hide_kg", "fat_kg", "horn_kg")),
}


MESOAMERICAN_STOCK_AND_GAME_NODES = ("fud_turkey_flock", "fud_dog_pack", "fud_game_hunting", "fud_fowling")


def stock_rows():
    with open(os.path.join(ROOT, "data", "world", "living_stock.json"), encoding="utf-8") as handle:
        return json.load(handle)["materials"]


class HerdRecipesMakeProductsTogether(unittest.TestCase):

    def setUp(self):
        self.production = demand.production_data()
        self.rows = stock_rows()

    def test_no_recipe_makes_a_herd_product_alone(self):
        for key, entry in self.production.items():
            made = [good for good in entry["outputs"] if good in HERD_PRODUCTS]
            if made and key not in HERDS:
                self.assertTrue(key.endswith("_kg") and len(entry["outputs"]) > 1 and "meat_kg" in entry["outputs"],
                                "%s makes %s outside a herd recipe" % (key, made))

    def test_each_herd_recipe_outputs_its_products_together(self):
        for key, (_stock, products) in HERDS.items():
            outputs = self.production[key]["outputs"]
            for good in products:
                self.assertGreater(outputs.get(good, 0.0), 0.0, "%s lacks %s" % (key, good))

    def test_wool_expands_hides_and_meat(self):
        # one recipe is the only source of wool, so more wool means more hides and meat in the same ratio
        makers = [entry for entry in self.production.values() if "wool_kg" in entry["outputs"]]
        self.assertEqual(len(makers), 1)
        outputs = makers[0]["outputs"]
        for factor in (1.0, 3.0):
            self.assertAlmostEqual(outputs["hide_kg"] * factor / (outputs["wool_kg"] * factor),
                                   outputs["hide_kg"] / outputs["wool_kg"])
            self.assertGreater(outputs["meat_kg"] * factor, 0.0)

    def test_outputs_follow_the_species_row(self):
        for key, (stock, _products) in HERDS.items():
            row, entry = self.rows[stock], self.production[key]
            outputs = entry["outputs"]
            slaughtered = HERD_HEAD * row["offtake_per_head_year"] * (1.0 - row.get("draught_share_of_offtake", 0.0))
            carcass = row["live_weight_kg_per_head"] * row["dressing_fraction"]
            fat = carcass * row["fat_share_of_carcass"]
            self.assertAlmostEqual(outputs["fat_kg"], slaughtered * fat, places=3)
            self.assertAlmostEqual(outputs["meat_kg"], slaughtered * (carcass - fat), places=3)
            self.assertAlmostEqual(
                outputs["hide_kg"], slaughtered * row["live_weight_kg_per_head"] * row["hide_share_of_live_weight"],
                places=3)
            self.assertAlmostEqual(outputs.get("wool_kg", 0.0), HERD_HEAD * row.get("fleece_kg_per_head_year", 0.0),
                                   places=3)
            self.assertAlmostEqual(outputs.get("milk_kg", 0.0), HERD_HEAD * row.get("milk_kg_per_head_year", 0.0),
                                   places=3)
            self.assertAlmostEqual(outputs.get("horn_kg", 0.0), slaughtered * row.get("horn_kg_per_animal", 0.0),
                                   places=3)
            self.assertAlmostEqual(entry["inputs"]["salt_kg"], HERD_HEAD * row["salt_kg_per_head_year"], places=3)
            self.assertAlmostEqual(entry["land_hectare_years"], HERD_HEAD / row["head_per_hectare"], places=3)

    def test_the_slaughtered_share_weighs_more_than_what_it_yields(self):
        for key, (stock, _products) in HERDS.items():
            row, outputs = self.rows[stock], self.production[key]["outputs"]
            live = HERD_HEAD * row["offtake_per_head_year"] * row["live_weight_kg_per_head"]
            carcass_goods = sum(outputs.get(good, 0.0) for good in ("meat_kg", "fat_kg", "hide_kg", "horn_kg"))
            self.assertLess(carcass_goods, live, key)
            self.assertLess(outputs["meat_kg"] + outputs["fat_kg"],
                            live * row["dressing_fraction"] + 1e-6, key)

    def test_offtake_is_what_the_herd_breeds(self):
        for _key, (stock, _products) in HERDS.items():
            row = self.rows[stock]
            self.assertLessEqual(row["offtake_per_head_year"], row["natural_increase"] - row["annual_loss"], stock)
            self.assertEqual(row["grows_on"], "pasture")
            self.assertGreater(len(row["source"]), 40)

    def test_herd_stock_is_the_live_weight_of_the_head_a_run_keeps(self):
        for key, (stock, _products) in HERDS.items():
            self.assertAlmostEqual(self.production[key]["herd_stock"][stock],
                                   HERD_HEAD * self.rows[stock]["live_weight_kg_per_head"])

    def test_meat_feeds_people_less_than_wheat_and_tallow_is_no_food(self):
        with open(os.path.join(ROOT, "data", "world", "needs.json"), encoding="utf-8") as handle:
            goods = json.load(handle)["goods"]
        meat = goods["meat_kg"]["satisfies"]["food"]
        self.assertTrue(0.0 < meat < goods["wheat_kg"]["satisfies"]["food"])
        self.assertNotIn("food", goods["fat_kg"]["satisfies"])


class SocietyWithoutTheAnimalCannotMakeItsProducts(unittest.TestCase):

    def setUp(self):
        self.nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        self.civilisations = start_check.load_civilisations(ROOT)
        self.production = load_production_catalog(ROOT)

    def test_every_herd_recipe_is_gated_on_holding_the_species(self):
        for key, (stock, _products) in HERDS.items():
            gate = self.production[key]["requires_node"]
            self.assertIsNotNone(gate, key)
            self.assertIn(stock, self.nodes[gate]["holds"], key)

    def test_a_civilisation_with_no_sheep_or_cattle_holds_no_herd_gate(self):
        mexica = self.civilisations["mexica_1500"]
        for key, (stock, _products) in HERDS.items():
            self.assertNotIn(self.production[key]["requires_node"], mexica["starting_techs"], key)
            self.assertEqual((mexica.get("opening_stock") or {}).get(stock, 0.0), 0.0, stock)

    def test_no_other_recipe_makes_a_herd_product_without_a_gate(self):
        mexica_techs = set(self.civilisations["mexica_1500"]["starting_techs"])
        for key, entry in self.production.items():
            if any(good in HERD_PRODUCTS for good in entry["outputs"]):
                gate = entry.get("requires_node", None)
                if gate in MESOAMERICAN_STOCK_AND_GAME_NODES:
                    continue  # the animals and game the Mexica do hold (Complaints/654)
                self.assertTrue(gate is not None and gate not in mexica_techs, key)


if __name__ == "__main__":
    unittest.main()
