"""SCENARIO (Complaint 640): for Complaint 543 in a whole game: the yearly step of a Rome game moves the soil nitrogen stock of its held
cropland, and a worn stock lowers what the society can feed. The rules and the save round trip are in
test_soil_nitrogen_held_land."""
import unittest

from .harness import *  # noqa: F401,F403
from sim.geography.api import crop_site, tiles_held


class SoilNitrogenWholeGameTests(unittest.TestCase):
    def test_a_year_of_cropping_draws_the_held_cropland_down(self):
        game = unopened_sim(civ="rome_100ad", events=False)
        self.assertEqual(game.state.economy.soil_nitrogen, {})
        game.step_soil_nitrogen()
        cropped = [tile for tile in tiles_held(game.civ, game.world_map)
                   if crop_site(tile, 0.5, game.world_map).yield_factor > 0.0]
        stock = game.state.economy.soil_nitrogen
        self.assertTrue(cropped)
        self.assertTrue(all(0.0 < stock[tile] < 1.0 for tile in cropped))

    def test_a_worn_tile_feeds_fewer_people(self):
        game = unopened_sim(civ="rome_100ad", events=False)
        before = game.society_food_potential()
        game.state.economy.soil_nitrogen = {tile: 0.3 for tile in tiles_held(game.civ, game.world_map)}
        after = game.society_food_potential()
        self.assertLess(sum(after.values()), sum(before.values()))


if __name__ == "__main__":
    unittest.main()
