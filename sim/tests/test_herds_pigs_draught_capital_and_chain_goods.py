"""Complaints 532 and 533: the pig herd, oxen as a herd product, the herd held as capital, and the chain goods
(nails, roof tiles, lard). Each test reads built inputs or the shipped data and calls the rule."""
QUICK_TOPIC = True

import json
import os
import unittest

from sim.engine import civ_start_check as start_check
from sim.prices import solve_prices_core as core
from sim.engine.catalog import load_production_catalog
from sim.prices.joint_allocation import allocate_joint_cost
from sim.engine.need_data import load_needs
from sim.engine.tree_source import load_base_tree

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERD_HEAD = 100.0
HERD_RECIPES = {"wool_kg": "sheep_kg", "milk_kg": "goat_kg", "meat_kg": "cattle_kg", "lard_kg": "pig_kg"}


def rows():
    with open(os.path.join(ROOT, "data", "world", "living_stock.json"), encoding="utf-8") as handle:
        return json.load(handle)["materials"]


class PigHerdTests(unittest.TestCase):

    def setUp(self):
        self.production = load_production_catalog(ROOT)
        self.row = rows()["pig_kg"]

    def test_a_pig_herd_makes_pork_lard_and_hides_together_from_the_row(self):
        outputs = self.production["lard_kg"]["outputs"]
        slaughtered = HERD_HEAD * self.row["offtake_per_head_year"]
        carcass = self.row["live_weight_kg_per_head"] * self.row["dressing_fraction"]
        lard = carcass * self.row["fat_share_of_carcass"]
        self.assertAlmostEqual(outputs["lard_kg"], slaughtered * lard, places=2)
        self.assertAlmostEqual(outputs["meat_kg"], slaughtered * (carcass - lard), places=2)
        self.assertAlmostEqual(outputs["hide_kg"], slaughtered * self.row["live_weight_kg_per_head"]
                               * self.row["hide_share_of_live_weight"], places=2)
        self.assertAlmostEqual(self.production["lard_kg"]["land_hectare_years"], HERD_HEAD / self.row["head_per_hectare"], places=3)

    def test_offtake_is_what_the_herd_breeds_and_the_row_names_its_sources(self):
        self.assertLessEqual(self.row["offtake_per_head_year"], self.row["natural_increase"] - self.row["annual_loss"])
        self.assertIn("Varro", self.row["source"])
        self.assertIn("labelled heuristics", self.row["source"])

    def test_the_herd_is_held_by_the_gate_node_and_stock_follows_the_row(self):
        nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        entry = self.production["lard_kg"]
        self.assertIn("pig_kg", nodes[entry["requires_node"]]["holds"])
        self.assertAlmostEqual(entry["herd_stock"]["pig_kg"], HERD_HEAD * self.row["live_weight_kg_per_head"])
        civilisations = start_check.load_civilisations(ROOT)
        self.assertIn(entry["requires_node"], civilisations["rome_100ad"]["starting_techs"])
        self.assertNotIn(entry["requires_node"], civilisations["mexica_1500"]["starting_techs"])

    def test_lard_feeds_people_and_bristle_is_not_invented(self):
        goods = load_needs(ROOT)["goods"]
        self.assertGreater(goods["lard_kg"]["satisfies"]["food"], 0.0)
        self.assertNotIn("bristle_kg", {good for entry in self.production.values() for good in entry["outputs"]})


class DraughtFromTheHerdTests(unittest.TestCase):

    def test_oxen_are_a_joint_product_taken_out_of_the_slaughter(self):
        row, entry = rows()["cattle_kg"], load_production_catalog(ROOT)["meat_kg"]
        offtake = HERD_HEAD * row["offtake_per_head_year"]
        draught_head = offtake * row["draught_share_of_offtake"]
        self.assertAlmostEqual(entry["outputs"]["draught_animal_kg"], draught_head * row["live_weight_kg_per_head"], places=2)
        carcass = row["live_weight_kg_per_head"] * row["dressing_fraction"]
        fat = carcass * row["fat_share_of_carcass"]
        self.assertAlmostEqual(entry["outputs"]["meat_kg"], (offtake - draught_head) * (carcass - fat), places=2)
        self.assertGreater(draught_head, 0.0)
        self.assertLess(draught_head, offtake)


class HerdIsCapitalTests(unittest.TestCase):

    def test_every_herd_recipe_charges_the_stock_it_holds_with_a_life_of_one_over_its_loss(self):
        production, stock_rows = load_production_catalog(ROOT), rows()
        for key, stock in HERD_RECIPES.items():
            entry = production[key]
            (capital,) = entry["capital"]
            self.assertEqual(capital["build_materials"], {stock: entry["herd_stock"][stock]}, key)
            self.assertAlmostEqual(capital["service_life_years"], 1.0 / stock_rows[stock]["annual_loss"], places=3)
            self.assertAlmostEqual(capital["annual_output_at_basis"], max(entry["outputs"].values()))

    def test_the_yearly_charge_per_batch_is_the_herd_value_times_the_loss(self):
        production, stock_rows = load_production_catalog(ROOT), rows()
        for key, stock in HERD_RECIPES.items():
            entry = production[key]
            price = 3.0
            per_unit = core._capital_cost_hours_per_unit(entry["capital"], {stock: price}, {}, 0.0)
            batch = per_unit * max(entry["outputs"].values())
            self.assertAlmostEqual(batch, entry["herd_stock"][stock] * price * stock_rows[stock]["annual_loss"], places=2, msg=key)

    def test_a_herd_that_cannot_be_priced_has_no_capital_cost(self):
        entry = load_production_catalog(ROOT)["lard_kg"]
        self.assertIsNone(core._capital_cost_hours_per_unit(entry["capital"], {}, {}, 0.0))


class JointCostSplitTests(unittest.TestCase):

    def test_a_reference_price_splits_the_batch_by_value_and_the_batch_is_recovered(self):
        outputs = load_production_catalog(ROOT)["lard_kg"]["outputs"]
        waste = {"manure_kg"}
        by_mass = allocate_joint_cost(outputs, 1000.0, waste_materials=waste)
        by_value = allocate_joint_cost(outputs, 1000.0, {"lard_kg": 5.0, "meat_kg": 2.0, "hide_kg": 1.0}, waste_materials=waste)
        for prices in (by_mass, by_value):
            self.assertAlmostEqual(sum(prices[good] * outputs[good] for good in outputs), 1000.0, places=4)
        self.assertGreater(by_value["lard_kg"] / by_value["meat_kg"], by_mass["lard_kg"] / by_mass["meat_kg"])
        self.assertAlmostEqual(by_mass["lard_kg"], by_mass["meat_kg"])


class ChainGoodsTests(unittest.TestCase):

    def setUp(self):
        self.production = load_production_catalog(ROOT)
        self.needs = load_needs(ROOT)["goods"]

    def users_of(self, good):
        return sorted(key for key, entry in self.production.items() if good in (entry.get("inputs") or {})
                      or any(good in way for capital in entry.get("capital") or [] for way in [capital.get("build_materials", {})]))

    def test_each_new_good_has_a_maker_and_a_user(self):
        for good in ("nails_kg", "roof_tile_kg"):
            makers = [key for key, entry in self.production.items() if good in entry["outputs"]]
            self.assertTrue(makers, good)
            self.assertTrue(self.users_of(good), good)
        self.assertTrue([key for key, entry in self.production.items() if "lard_kg" in entry["outputs"]])
        self.assertTrue(self.needs["lard_kg"]["satisfies"])

    def test_nails_are_made_from_bar_and_used_by_carts_and_frames(self):
        self.assertIn("iron_bar_kg", self.production["nails_kg"]["inputs"])
        self.assertGreaterEqual(set(self.users_of("nails_kg")), {"cart", "timber_frame_m3"})

    def test_tiles_are_fired_ware_used_by_masonry_roofs(self):
        self.assertIn("ceramic_kg", self.production["roof_tile_kg"]["inputs"])
        self.assertGreaterEqual(set(self.users_of("roof_tile_kg")), {"brick_wall_m3", "stone_wall_m3"})

    def test_the_cart_keeps_its_iron_mass(self):
        inputs = self.production["cart"]["inputs"]
        self.assertAlmostEqual(inputs["iron_bar_kg"] + inputs["nails_kg"], 15.0)


if __name__ == "__main__":
    unittest.main()
