"""Complaint 537: a crop's own climate envelopes decide how well it yields on a tile against the reference field.
`food_crops.crop_suitability` on the base map's tiles, with envelopes written out here."""
QUICK_TOPIC = True

import unittest

from sim.geography import food_crops
from sim.geography.api import open_map

WET_WARM_CROP = food_crops.CropEnvelopes(
    [{"layer": "mean_temperature_c", "optimal": [20, 30], "tolerated": [10, 38]}],
    [{"layer": "annual_precipitation_mm", "optimal": [1200, 3000], "tolerated": [500, 5000]}])
DRY_CROP = food_crops.CropEnvelopes(
    [{"layer": "mean_temperature_c", "optimal": [10, 26], "tolerated": [3, 38]}],
    [{"layer": "annual_precipitation_mm", "optimal": [350, 900], "tolerated": [150, 2000]}])


class CropSuitabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world_map = open_map()
        cls.tiles = sorted(cls.world_map.tiles)

    def layer(self, tile_id, layer_id):
        return food_crops.tile_layers.number(self.world_map, tile_id, layer_id, None)

    def tile_where(self, test):
        for tile_id in self.tiles:
            rain, warmth = self.layer(tile_id, "annual_precipitation_mm"), self.layer(tile_id, "mean_temperature_c")
            if rain is not None and warmth is not None and test(rain, warmth) and food_crops.crop_site(self.world_map, tile_id, 1.0).yield_factor > 0.0:
                return tile_id
        self.fail("no tile on the map meets the test")

    def test_the_crop_that_wants_wet_ground_suits_a_wet_warm_tile_better_than_the_dry_crop_does(self):
        tile_id = self.tile_where(lambda rain, warmth: rain > 2200 and 22 < warmth < 28)
        self.assertGreater(food_crops.crop_suitability(self.world_map, tile_id, WET_WARM_CROP),
                           food_crops.crop_suitability(self.world_map, tile_id, DRY_CROP))

    def test_the_dry_crop_suits_a_dry_tile_better_than_the_wet_crop_does(self):
        tile_id = self.tile_where(lambda rain, warmth: 300 < rain < 500 and 12 < warmth < 24)
        self.assertGreater(food_crops.crop_suitability(self.world_map, tile_id, DRY_CROP),
                           food_crops.crop_suitability(self.world_map, tile_id, WET_WARM_CROP))

    def test_the_reference_envelopes_give_one(self):
        tile_id = self.tile_where(lambda rain, warmth: rain > 700 and 12 < warmth < 25)
        reference = food_crops.CropEnvelopes(self.world_map.catalogues["parameters"]["food_crop_temperature_envelope"]["value"],
                                             self.world_map.catalogues["parameters"]["food_crop_water_envelope"]["value"])
        self.assertAlmostEqual(food_crops.crop_suitability(self.world_map, tile_id, reference), 1.0)

    def test_a_crop_site_with_envelopes_is_kept_apart_from_the_reference_one(self):
        tile_id = self.tile_where(lambda rain, warmth: 300 < rain < 500 and 12 < warmth < 24)
        reference = food_crops.crop_site(self.world_map, tile_id, 1.0)
        wet = food_crops.crop_site(self.world_map, tile_id, 1.0, envelopes=WET_WARM_CROP)
        self.assertNotEqual(reference.yield_factor, wet.yield_factor)
        self.assertEqual(reference, food_crops.crop_site(self.world_map, tile_id, 1.0))


if __name__ == "__main__":
    unittest.main()
