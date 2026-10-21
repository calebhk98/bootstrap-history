"""The game keeps the wild stock between years (Complaint 411): a year's step regrows a drawn-down stock when nobody
hunts, and leaves a full one alone. Complaint 640: the yearly step is called on a stand-in game over the small fixture
map; the regrowth rule itself is test_geography_wild_stock, and the save round trip is test_wild_stock_whole_game_scenario."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.food_supply import FoodSupplyMixin
from sim.geography import api
from sim.tests.test_geography_food_gaps import STEPPE, mini_map


class _Geography:
    """What `step_wild_stock` asks of geography: the fixture map's regrowth, and no hunted source."""

    def __init__(self, world_map):
        self._map = world_map

    def game_food_sources(self):
        return []

    def regrow_wild_stock(self, stock):
        return api.regrow_wild_stock(stock, self._map)


class _Game(FoodSupplyMixin):
    def __init__(self, wild_stock):
        self.state = types.SimpleNamespace(economy=types.SimpleNamespace(wild_stock=wild_stock))
        self.geography = _Geography(mini_map({"a": (STEPPE, {}, [])}))

    def _gathering_caps(self):
        return {}


class WildStockStepTests(unittest.TestCase):

    def test_the_stock_regrows_in_the_yearly_step_when_nobody_hunts(self):
        game = _Game({"a": {"steppe_grazers": 0.4}})
        game.step_wild_stock()
        self.assertGreater(game.state.economy.wild_stock["a"]["steppe_grazers"], 0.4)

    def test_an_empty_stock_stays_empty(self):
        game = _Game({})
        game.step_wild_stock()
        self.assertEqual(game.state.economy.wild_stock, {})


if __name__ == "__main__":
    unittest.main()
