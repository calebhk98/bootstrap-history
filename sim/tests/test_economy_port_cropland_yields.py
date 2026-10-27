"""`port_setup.cropland_yields`: only the recipes that grow on arable land carry a tile's yield factor, one per
tile; pasture, forest and mine recipes do not. Hand-written production entries and tiles; no game."""
QUICK_TOPIC = True

import unittest

from sim.economy.setup import recipe_tile_key
from sim.markets import port_setup
from sim.economy.types import TileSpec

PRODUCTION = {"wheat": {"extracted_from": "arable land"},
              "barley": {"extracted_from": "arable land (spring sown)"},
              "pasture": {"extracted_from": "grazing land"},
              "mine": {}}


def tiles():
    return {"good": TileSpec("good", 40.0, 10.0, 100.0, False, (), 0.5, 1.4),
            "poor": TileSpec("poor", 40.0, 11.0, 100.0, False, (), 0.5, 0.6)}


class CroplandYieldsTests(unittest.TestCase):
    def setUp(self):
        self.yields = port_setup.cropland_yields(PRODUCTION, PRODUCTION, tiles())

    def test_a_crop_recipe_carries_each_tiles_fertility(self):
        self.assertEqual(self.yields[recipe_tile_key("wheat", "good")], 1.4)
        self.assertEqual(self.yields[recipe_tile_key("wheat", "poor")], 0.6)

    def test_a_source_that_adds_a_note_after_arable_land_still_crops(self):
        self.assertIn(recipe_tile_key("barley", "good"), self.yields)

    def test_pasture_and_mine_recipes_carry_no_tile_yield(self):
        recipes_keyed = {key.partition("@")[0] for key in self.yields}
        self.assertEqual(recipes_keyed, {"wheat", "barley"})


if __name__ == "__main__":
    unittest.main()
