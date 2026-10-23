"""Scenarios (Complaint 411 and 640): the wild stock a played game keeps survives a save and load, and the yearly step of
a played game regrows it when nobody hunts. The rules are in test_wild_stock_whole_game and test_geography_wild_stock."""
import os
import tempfile
import unittest

from .harness import *  # noqa: F401,F403
from sim.engine.saveload import load_state, save_state


class WildStockWholeGameTests(unittest.TestCase):
    def test_the_stock_round_trips_through_a_save(self):
        game = unopened_sim(civ="rome_100ad", events=False)
        tile_id = next(iter(game.world_map.tiles))
        game.state.economy.wild_stock = {tile_id: {"steppe_grazers": 0.4}}
        path = os.path.join(tempfile.mkdtemp(), "save.json")
        save_state(game, path)
        reloaded = unopened_sim(civ="rome_100ad", events=False)
        load_state(reloaded, path)
        self.assertEqual(reloaded.state.economy.wild_stock, {tile_id: {"steppe_grazers": 0.4}})

    def test_the_yearly_step_of_a_played_game_regrows_the_stock_when_nobody_hunts(self):
        game = unopened_sim(civ="rome_100ad", events=False)
        tile_id = next(iter(game.world_map.tiles))
        game.state.economy.wild_stock = {tile_id: {"steppe_grazers": 0.4}}
        game.step()
        self.assertGreater(game.state.economy.wild_stock[tile_id]["steppe_grazers"], 0.4)


if __name__ == "__main__":
    unittest.main()
