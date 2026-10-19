"""Complaints/535: salt is a physiological need with a sourced floor, and cheese turns perishable milk into a keepable good with salt."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.world import demand, need_basket

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def world_file(name):
    with open(os.path.join(ROOT, "data", "world", name), encoding="utf-8") as handle:
        return json.load(handle)


class SaltIsAnEatenNeed(unittest.TestCase):

    def test_salt_need_has_a_sourced_floor(self):
        need = world_file("needs.json")["needs"]["salt"]
        self.assertGreater(need_basket.need_floor(need), 0.0)
        self.assertGreater(need["subsistence_basis"], "")
        self.assertIn("Institute of Medicine", need["subsistence_basis"])

    def test_basket_buys_salt_at_an_opening(self):
        needs = world_file("needs.json")
        basket = need_basket.make_basket(needs, demand.production_data())
        spec = {spec.need_id: spec for spec in basket.needs}["salt"]
        self.assertIn("salt_kg", [good for good, _effect in spec.goods])
        self.assertAlmostEqual(spec.subsistence_per_person, need_basket.need_floor(needs["needs"]["salt"]))

    def test_floor_is_below_the_satiation_limit(self):
        need = world_file("needs.json")["needs"]["salt"]
        self.assertLess(need_basket.need_floor(need), need["satiation_per_capita_per_year"])


class CheesePreservesMilk(unittest.TestCase):

    def entry(self):
        return demand.production_data()["cheese_kg"]

    def test_recipe_uses_salt_and_milk_and_balances_mass(self):
        entry = self.entry()
        self.assertIn("salt_kg", entry["inputs"])
        self.assertIn("milk_kg", entry["inputs"])
        mass_in = sum(entry["inputs"].values())
        mass_out = sum(entry["outputs"].values())
        self.assertGreaterEqual(mass_in, mass_out)       # whey leaves, nothing is made from nothing
        self.assertLess(mass_out, 0.5 * mass_in)

    def test_output_spoils_less_than_input(self):
        rates = world_file("spoilage.json")["rates_per_year"]
        self.assertLess(rates["cheese_kg"]["rate"], rates["milk_kg"]["rate"])
        self.assertTrue(rates["cheese_kg"]["source"])


class HerdsLickSalt(unittest.TestCase):

    def test_every_herd_recipe_takes_salt_from_the_species_row(self):
        herds = json.load(open(os.path.join(ROOT, "data", "production", "95_herds.json"), encoding="utf-8"))["materials"]
        rows = world_file("living_stock.json")["materials"]
        for name, recipe in herds.items():
            if "herd_stock" not in recipe:
                continue
            herd_kind = list(recipe["herd_stock"])[0]
            self.assertAlmostEqual(recipe["inputs"]["salt_kg"], rows[herd_kind]["salt_kg_per_head_year"] * 100.0, places=3, msg=name)


class SaltedMeatKeeps(unittest.TestCase):

    def entry(self):
        return demand.production_data()["salted_meat_kg"]

    def test_recipe_uses_meat_and_salt_and_loses_water(self):
        entry = self.entry()
        self.assertIn("meat_kg", entry["inputs"])
        self.assertGreater(entry["inputs"]["salt_kg"], 0.0)
        self.assertLess(sum(entry["outputs"].values()), sum(entry["inputs"].values()))
        self.assertIn(entry["conf"], ("C", "D"))

    def test_output_spoils_far_less_than_fresh_meat(self):
        rates = world_file("spoilage.json")["rates_per_year"]
        self.assertLess(rates["salted_meat_kg"]["rate"], 0.1 * rates["meat_kg"]["rate"])
        self.assertTrue(rates["salted_meat_kg"]["source"])

    def test_salted_meat_is_food(self):
        satisfies = world_file("needs.json")["goods"]["salted_meat_kg"]["satisfies"]
        self.assertIn("food", satisfies)


class CheeseLabourIsLabelled(unittest.TestCase):

    def test_labour_figure_states_its_source_search(self):
        entry = demand.production_data()["cheese_kg"]
        self.assertEqual(entry["conf"], "D")
        self.assertIn("no published time study", entry["yield_basis"])


if __name__ == "__main__":
    unittest.main()
