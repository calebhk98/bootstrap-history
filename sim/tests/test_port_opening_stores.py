"""The opening stocks of durable stores, derived from a civilisation's deposits (no game is built)."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.engine.economy_port_stores import opening_store_values
from sim.geography.api import open_map, tiles_held

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "civilizations")


def stores_of(civ_file):
    with open(os.path.join(DATA, civ_file), encoding="utf-8") as handle:
        civ = json.load(handle)
    world_map = open_map()
    return opening_store_values(world_map, tiles_held(civ, world_map), int(civ["year"]))


class OpeningStoreValueTests(unittest.TestCase):
    def test_a_country_with_dated_deposits_has_workings_for_the_metal(self):
        stores = stores_of("rome_100ad.json")
        self.assertTrue(stores["gold_kg"]["workings"])
        self.assertTrue(stores["silver_kg"]["workings"])

    def test_a_country_with_no_deposit_of_a_metal_says_so_and_has_no_workings(self):
        stores = stores_of("han_china_100ad.json")
        self.assertEqual(stores["gold_kg"]["workings"], [])
        self.assertIn("no known deposit", stores["gold_kg"]["gap"])

    def test_a_resource_counted_in_tonnes_is_not_read_as_kilograms(self):
        for civ_file in ("rome_100ad.json", "england_1300.json"):
            self.assertEqual(stores_of(civ_file)["coal_kg"]["workings"], [])

    def test_a_resource_that_yields_several_goods_chooses_none(self):
        stores = stores_of("rome_100ad.json")
        self.assertEqual(stores["iron_bar_kg"]["workings"], [])
        self.assertIn("several goods", stores["iron_bar_kg"]["gap"])


if __name__ == "__main__":
    unittest.main()
