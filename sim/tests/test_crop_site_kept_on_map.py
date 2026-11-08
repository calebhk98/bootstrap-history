"""A tile's crop site is a pure function of the map and four numbers, so the map keeps each answer: the kept answer equals the
computed one for every tile, a repeat is not computed again, and a second map (a mod's changed parameter) never reads the first's."""
QUICK_TOPIC = True

import copy
import unittest

from sim.geography import food_crops
from sim.geography.api import open_map


class CropSiteKeptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world_map = open_map()

    def test_kept_answer_equals_the_computed_one_for_every_tile(self):
        for tile_id in sorted(self.world_map.tiles):
            for share, nutrient, tillage in ((0.5, 1.0, 1.0), (0.75, 0.8, 0.4)):
                kept = food_crops.crop_site(self.world_map, tile_id, share, nutrient, tillage)
                computed = food_crops.computed_crop_site(self.world_map, tile_id, share, nutrient, tillage)
                self.assertEqual(kept, computed)

    def test_a_repeat_is_the_kept_object(self):
        tile_id = sorted(self.world_map.tiles)[0]
        first = food_crops.crop_site(self.world_map, tile_id, 0.5)
        self.assertIs(first, food_crops.crop_site(self.world_map, tile_id, 0.5))

    def test_a_different_argument_is_a_different_answer_not_the_kept_one(self):
        tile_id = max(self.world_map.tiles, key=lambda tile: food_crops.computed_crop_site(self.world_map, tile, 0.5).cropped_hectares)
        low = food_crops.crop_site(self.world_map, tile_id, 0.25)
        high = food_crops.crop_site(self.world_map, tile_id, 0.75)
        self.assertLess(low.cropped_hectares, high.cropped_hectares)

    def test_another_map_does_not_read_the_first_maps_answers(self):
        tile_id = max(self.world_map.tiles, key=lambda tile: food_crops.computed_crop_site(self.world_map, tile, 0.5).cropped_hectares)
        food_crops.crop_site(self.world_map, tile_id, 0.5)
        other = copy.deepcopy(self.world_map)
        other.catalogues["parameters"]["food_irrigated_cropped_share"]["value"] = 0.0
        other.catalogues["parameters"]["food_forest_fallow_years"]["value"] = 1e9
        other.__dict__.pop("_crop_site_cache", None)    # a map built from changed data starts with no kept answers
        other.__dict__.pop("_layer_cache", None)
        self.assertEqual(food_crops.crop_site(other, tile_id, 0.5), food_crops.computed_crop_site(other, tile_id, 0.5))


if __name__ == "__main__":
    unittest.main()
