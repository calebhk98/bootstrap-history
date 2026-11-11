"""`port_setup.cropland_yields`: only the recipes that grow on arable land carry a tile's yield factor, one per
tile; pasture, forest and mine recipes do not. Hand-written production entries and tiles; no game."""
QUICK_TOPIC = True

import unittest

from sim.economy.setup import recipe_tile_key
from sim.markets import port_cropland, port_setup
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

    def test_a_crops_suitability_scales_the_tiles_fertility_for_that_crop_only(self):
        suitability = {recipe_tile_key("barley", "good"): 0.5}
        yields = port_setup.cropland_yields(PRODUCTION, PRODUCTION, tiles(), suitability)
        self.assertEqual(yields[recipe_tile_key("barley", "good")], 0.7)
        self.assertEqual(yields[recipe_tile_key("wheat", "good")], 1.4)
        self.assertEqual(yields[recipe_tile_key("barley", "poor")], 0.6)


class FollowedFactorsTests(unittest.TestCase):
    def test_a_changed_tile_gives_each_crop_the_new_fertility_times_its_suitability(self):
        factors = {recipe_tile_key("wheat", "good"): 1.4, recipe_tile_key("rice", "good"): 0.7, recipe_tile_key("rice", "poor"): 0.3}
        suitability = {recipe_tile_key("rice", "good"): 0.5, recipe_tile_key("rice", "poor"): 0.5}
        followed = port_cropland.followed_factors(factors, {"good": 2.0}, suitability)
        self.assertEqual(followed, {recipe_tile_key("wheat", "good"): 2.0, recipe_tile_key("rice", "good"): 1.0,
                                    recipe_tile_key("rice", "poor"): 0.3})


if __name__ == "__main__":
    unittest.main()
