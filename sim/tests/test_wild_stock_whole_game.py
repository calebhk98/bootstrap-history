"""The game keeps the wild stock between years (Complaint 411): a year's step regrows a drawn-down stock when nobody
hunts, and leaves a full one alone. Complaint 640: the yearly step is called on the module over the small fixture
map; the regrowth rule itself is test_geography_wild_stock, and the save round trip is test_wild_stock_save_and_phase."""
QUICK_TOPIC = True

import unittest

from sim.agriculture.state import AgricultureWorld
from sim.geography import api
from sim.tests import agriculture_stand_in
from sim.tests.test_geography_food_gaps import STEPPE, mini_map


def game(wild_stock):
    """The agriculture module over the fixture map's regrowth, with no hunted source and no gatherers."""
    world_map = mini_map({"a": (STEPPE, {}, [])})
    return agriculture_stand_in.build(world=AgricultureWorld(wild_stock=wild_stock), views={
        "game_food_sources": [], "society_labour_hours": {}, "trade_registry": {},
        "regrow_wild_stock": lambda stock: api.regrow_wild_stock(stock, world_map)})


class WildStockStepTests(unittest.TestCase):

    def test_the_stock_regrows_in_the_yearly_step_when_nobody_hunts(self):
        farm = game({"a": {"steppe_grazers": 0.4}})
        farm.step_wild_stock()
        self.assertGreater(farm.world.wild_stock["a"]["steppe_grazers"], 0.4)

    def test_an_empty_stock_stays_empty(self):
        farm = game({})
        farm.step_wild_stock()
        self.assertEqual(farm.world.wild_stock, {})


if __name__ == "__main__":
    unittest.main()
