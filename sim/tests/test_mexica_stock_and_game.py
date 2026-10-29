"""Complaints/654: the Mexica start holds turkeys, dogs, deer hunting and fowling, so meat, fat, hides and
their goods are supplied through shipped chains; a start without those nodes cannot make them."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.engine import civ_basket_check as check
from sim.engine import civ_start_check as start_check
from sim.engine.catalog import load_production_catalog
from sim.content.api import load_needs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NODES = ("fud_turkey_flock", "fud_dog_pack", "fud_game_hunting", "fud_fowling")
SUPPLIED = ("meat_kg", "fat_kg", "leather_kg", "salted_meat_kg", "light_tallow_candle", "light_tallow_rushlight")


def _unsupplied(civilisation):
    production = load_production_catalog(ROOT)
    with open(os.path.join(ROOT, "data", "world", "foreign_economies.json"), encoding="utf-8") as handle:
        economies = json.load(handle)["economies"]
    goods = load_needs(ROOT)["goods"]
    return check.unsupplied_basket_goods("home", {"home": civilisation}, production, goods, economies)


class MexicaSuppliesMeatFatAndHides(unittest.TestCase):

    def setUp(self):
        self.mexica = start_check.load_civilisations(ROOT)["mexica_1500"]

    def test_mexica_holds_the_four_nodes(self):
        for node in NODES:
            self.assertIn(node, self.mexica["starting_techs"])

    def test_the_basket_check_finds_meat_fat_hide_goods_supplied(self):
        missing = _unsupplied(dict(self.mexica, year=self.mexica["year"]))
        for good in SUPPLIED:
            self.assertNotIn(good, missing, good)

    def test_the_declared_entries_for_those_goods_are_gone(self):
        for good in SUPPLIED:
            self.assertNotIn(good, self.mexica["unsupplied_basket_goods"], good)

    def test_a_start_without_the_nodes_cannot_supply_them(self):
        bare = dict(self.mexica, starting_techs=[t for t in self.mexica["starting_techs"] if t not in NODES])
        missing = _unsupplied(bare)
        for good in ("meat_kg", "fat_kg", "leather_kg", "salted_meat_kg"):
            self.assertIn(good, missing, good)

    def test_each_node_alone_supplies_meat_and_fat(self):
        for node in NODES:
            alone = dict(self.mexica, starting_techs=[t for t in self.mexica["starting_techs"] if t not in NODES] + [node])
            missing = _unsupplied(alone)
            self.assertNotIn("meat_kg", missing, node)
            self.assertNotIn("fat_kg", missing, node)

    def test_hides_come_from_the_dog_pack_and_the_hunt_only(self):
        production = load_production_catalog(ROOT)
        makers = {entry["requires_node"] for entry in production.values() if "hide_kg" in entry["outputs"]}
        self.assertTrue({"fud_dog_pack", "fud_game_hunting"} <= makers)
        self.assertNotIn("fud_turkey_flock", makers)


class RecipesFollowTheirSources(unittest.TestCase):

    def setUp(self):
        self.production = load_production_catalog(ROOT)
        with open(os.path.join(ROOT, "data", "world", "living_stock.json"), encoding="utf-8") as handle:
            self.rows = json.load(handle)["materials"]

    def test_joint_products_of_each_recipe(self):
        expected = {"feather_kg": ("feather_kg", "meat_kg", "fat_kg"), "hide_kg": ("hide_kg", "meat_kg", "fat_kg"),
                    "down_kg": ("down_kg", "meat_kg", "fat_kg"), "fat_kg": ("fat_kg", "meat_kg", "hide_kg")}
        for key, goods in expected.items():
            entry = self.production[key]
            self.assertIn(entry["requires_node"], NODES)
            self.assertEqual(set(goods), set(entry["outputs"]))
            for good in goods:
                self.assertGreater(entry["outputs"][good], 0.0)

    def test_stock_recipes_follow_the_species_row(self):
        for key, stock in (("feather_kg", "turkey_kg"), ("hide_kg", "dog_kg")):
            row, entry = self.rows[stock], self.production[key]
            slaughtered = 100.0 * row["offtake_per_head_year"]
            carcass = row["live_weight_kg_per_head"] * row["dressing_fraction"]
            fat = carcass * row["fat_share_of_carcass"]
            self.assertAlmostEqual(entry["outputs"]["fat_kg"], slaughtered * fat, places=2)
            self.assertAlmostEqual(entry["outputs"]["meat_kg"], slaughtered * (carcass - fat), places=2)
            self.assertAlmostEqual(entry["herd_stock"][stock], 100.0 * row["live_weight_kg_per_head"], places=2)
            self.assertLessEqual(row["offtake_per_head_year"], row["natural_increase"] - row["annual_loss"])
            self.assertIn("source", row)
            self.assertIn("no source found", row["source"])

    def test_deer_meat_is_the_ohio_butchering_yield(self):
        entry = self.production["fat_kg"]
        self.assertAlmostEqual(entry["outputs"]["meat_kg"] / 100.0, 52.19 * 0.45359237, places=2)
        self.assertIn("107.56 pounds field dressed", entry["yield_basis"])

    def test_the_stock_rows_are_held_by_the_nodes(self):
        tree = {node["id"]: node for node in json.load(open(os.path.join(ROOT, "data", "branches", "56_herd_stock.json")))}
        self.assertIn("turkey_kg", tree["fud_turkey_flock"]["holds"])
        self.assertIn("dog_kg", tree["fud_dog_pack"]["holds"])


if __name__ == "__main__":
    unittest.main()
