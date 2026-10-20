"""Complaint 543: the soil nitrogen stock lives in the game state, saves and loads, and the yearly step moves it.
Builds whole games, so it is a slow topic."""
import os
import tempfile
import unittest

from .harness import *  # noqa: F401,F403
from sim.engine.saveload import load_state, save_state
from sim.geography.api import crop_site, tiles_held


class SoilNitrogenWholeGameTests(unittest.TestCase):
    def test_the_stock_round_trips_through_a_save(self):
        game = sim(civ="rome_100ad", events=False)
        tile_id = next(iter(game.world_map.tiles))
        game.state.economy.soil_nitrogen = {tile_id: 0.6}
        path = os.path.join(tempfile.mkdtemp(), "save.json")
        save_state(game, path)
        reloaded = sim(civ="rome_100ad", events=False)
        load_state(reloaded, path)
        self.assertEqual(reloaded.state.economy.soil_nitrogen, {tile_id: 0.6})

    def test_a_year_of_cropping_draws_the_held_cropland_down(self):
        game = sim(civ="rome_100ad", events=False)
        self.assertEqual(game.state.economy.soil_nitrogen, {})
        game.step_soil_nitrogen()
        cropped = [tile for tile in tiles_held(game.civ, game.world_map)
                   if crop_site(tile, 0.5, game.world_map).yield_factor > 0.0]
        stock = game.state.economy.soil_nitrogen
        self.assertTrue(cropped)
        self.assertTrue(all(0.0 < stock[tile] < 1.0 for tile in cropped))

    def test_a_worn_tile_feeds_fewer_people(self):
        game = sim(civ="rome_100ad", events=False)
        before = game.society_food_potential()
        game.state.economy.soil_nitrogen = {tile: 0.3 for tile in tiles_held(game.civ, game.world_map)}
        after = game.society_food_potential()
        self.assertLess(sum(after.values()), sum(before.values()))


if __name__ == "__main__":
    unittest.main()
