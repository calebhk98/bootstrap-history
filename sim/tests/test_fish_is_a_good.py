"""Complaint 615: fresh fish is a good made by fishers, eaten as food at the calories the fisher's return implies; salted fish and garum keep."""
QUICK_TOPIC = True

import json
import os
import unittest

from sim.engine.catalog import load_production_catalog
from sim.world import demand, need_basket
from sim.world.shared_constants import WHEAT_ENERGY_KCAL_PER_KG

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PRODUCTION = load_production_catalog(_ROOT)


def world_file(name):
    with open(os.path.join(_ROOT, "data", "world", name), encoding="utf-8") as handle:
        return json.load(handle)


def kcal_per_kg(good):
    return world_file("needs.json")["goods"][good]["satisfies"]["food"] * WHEAT_ENERGY_KCAL_PER_KG


class FreshFishIsTraded(unittest.TestCase):

    def test_fishers_make_fish_from_their_own_hours(self):
        recipe = _PRODUCTION["fish_kg"]
        self.assertEqual(set(recipe["labour_hours"]), {"fisher"})
        self.assertEqual(recipe["inputs"], {})
        self.assertIn(recipe["conf"], ("C", "D"))

    def test_catch_calories_match_the_fishers_return_per_hour(self):
        trade = world_file("trades.json")["trades"]["fisher"]
        recipe = _PRODUCTION["fish_kg"]
        catch_kcal = recipe["outputs"]["fish_kg"] * kcal_per_kg("fish_kg")
        hours_kcal = recipe["labour_hours"]["fisher"] * trade["food_kcal_per_hour"]
        self.assertAlmostEqual(catch_kcal, hours_kcal, delta=0.01 * hours_kcal)

    def test_households_eat_fish(self):
        needs = world_file("needs.json")
        basket = need_basket.make_basket(needs, demand.production_data())
        spec = {spec.need_id: spec for spec in basket.needs}["food"]
        self.assertIn("fish_kg", [good for good, _effect in spec.goods])

    def test_fresh_fish_has_a_spoilage_row(self):
        self.assertGreater(world_file("spoilage.json")["rates_per_year"]["fish_kg"]["rate"], 0.0)


class PreservedFish(unittest.TestCase):

    def test_salted_fish_takes_fish_and_salt_and_conserves_calories(self):
        recipe = _PRODUCTION["salted_fish_kg"]
        self.assertGreater(recipe["inputs"]["fish_kg"], 0.0)
        self.assertGreater(recipe["inputs"]["salt_kg"], 0.0)
        self.assertLess(sum(recipe["outputs"].values()), sum(recipe["inputs"].values()))
        energy_in = recipe["inputs"]["fish_kg"] * kcal_per_kg("fish_kg")
        energy_out = recipe["outputs"]["salted_fish_kg"] * kcal_per_kg("salted_fish_kg")
        self.assertAlmostEqual(energy_out, energy_in, delta=0.01 * energy_in)    # curing adds no energy and loses none

    def test_preserved_fish_keeps_far_longer_than_fresh(self):
        rates = world_file("spoilage.json")["rates_per_year"]
        self.assertLess(rates["salted_fish_kg"]["rate"], 0.01 * rates["fish_kg"]["rate"])
        self.assertLess(rates["garum_kg"]["rate"], 0.01 * rates["fish_kg"]["rate"])
        for good in ("fish_kg", "salted_fish_kg", "garum_kg"):
            self.assertTrue(rates[good]["source"], good)

    def test_garum_ferments_fish_in_salt(self):
        recipe = _PRODUCTION["garum_kg"]
        self.assertGreater(recipe["inputs"]["fish_kg"], 0.0)
        self.assertGreater(recipe["inputs"]["salt_kg"], 0.0)
        self.assertLess(sum(recipe["outputs"].values()), sum(recipe["inputs"].values()))
        self.assertGreater(recipe["holding_years"], 0.0)

    def test_curing_hours_are_booked_to_a_real_trade(self):
        trades = world_file("trades.json")["trades"]
        for good in ("salted_fish_kg", "garum_kg"):
            for trade in _PRODUCTION[good]["labour_hours"]:
                self.assertIn(trade, trades, good)
                self.assertNotIn(trade, ("labourer", "artisan"), good)


if __name__ == "__main__":
    unittest.main()
