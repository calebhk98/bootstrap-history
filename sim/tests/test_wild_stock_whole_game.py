"""The game keeps the wild stock between years (Complaint 411): it survives a save and load, a year's step
leaves it alone while nobody hunts, and the game grows back after hunters stop. Builds whole games, so it is
a slow topic.
"""
import os
import tempfile
import unittest

from .harness import *  # noqa: F401,F403
from sim.engine.saveload import load_state, save_state


class WildStockWholeGameTests(unittest.TestCase):
    def test_the_stock_round_trips_through_a_save(self):
        game = sim(civ="rome_100ad", events=False)
        tile_id = next(iter(game.world_map.tiles))
        game.state.economy.wild_stock = {tile_id: {"steppe_grazers": 0.4}}
        path = os.path.join(tempfile.mkdtemp(), "save.json")
        save_state(game, path)
        reloaded = sim(civ="rome_100ad", events=False)
        load_state(reloaded, path)
        self.assertEqual(reloaded.state.economy.wild_stock, {tile_id: {"steppe_grazers": 0.4}})

    def test_the_stock_regrows_in_the_yearly_step_when_nobody_hunts(self):
        game = sim(civ="rome_100ad", events=False)
        tile_id = next(iter(game.world_map.tiles))
        game.state.economy.wild_stock = {tile_id: {"steppe_grazers": 0.4}}
        game.step()
        self.assertGreater(game.state.economy.wild_stock[tile_id]["steppe_grazers"], 0.4)


if __name__ == "__main__":
    unittest.main()
