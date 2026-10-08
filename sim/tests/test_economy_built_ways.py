"""Built roads reach the agent economy's carriage costs (Complaint 416): a way recorded between two tiles
lowers the haul between them, the setup carries the ways, the live economy rebuilds its carriage table when
a way is finished, and the spin-up cache key sees them.

sim/economy/tile_costs.py, sim/economy/setup.py, sim/economy/economy.py, sim/engine/economy_port_key.py.
"""
QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import api as economy_api
from sim.economy import tile_costs
from sim.economy.setup import EconomySetup
from sim.engine import economy_port_key
from sim.geography import api as geography_api
from sim.tests import economy_fixture
from sim.tests.test_economy_tile_costs import grid

RATES = {"cart": 0.19, "road": 0.1}


def road_between(tile_a, tile_b):
    return {geography_api.edge_key(tile_a, tile_b): {"road": True}}


def table(tiles, improvements=None, rates=None):
    return tile_costs.carriage_table(tiles, rates or RATES, world_map=tile_costs.world_map_of(tiles),
                                     improvements=improvements)


class CarriageTableTests(unittest.TestCase):
    def test_a_built_road_lowers_the_haul_between_its_ends(self):
        tiles = grid(3, 1)
        before = table(tiles).cost_per_tonne("t_0_0", "t_1_0")
        after = table(tiles, road_between("t_0_0", "t_1_0")).cost_per_tonne("t_0_0", "t_1_0")
        self.assertLess(after, before)

    def test_only_the_built_edge_gets_cheaper(self):
        tiles = grid(3, 1)
        plain, built = table(tiles), table(tiles, road_between("t_0_0", "t_1_0"))
        self.assertAlmostEqual(plain.cost_per_tonne("t_1_0", "t_2_0"), built.cost_per_tonne("t_1_0", "t_2_0"))
        self.assertLess(built.cost_per_tonne("t_0_0", "t_2_0"), plain.cost_per_tonne("t_0_0", "t_2_0"))

    def test_a_road_with_no_road_rate_is_not_used(self):
        tiles = grid(2, 1)
        carts_only = table(tiles, road_between("t_0_0", "t_1_0"), {"cart": 0.19})
        unbuilt = table(tiles, None, {"cart": 0.19})
        self.assertAlmostEqual(carts_only.cost_per_tonne("t_0_0", "t_1_0"), unbuilt.cost_per_tonne("t_0_0", "t_1_0"))


class SetupAndEconomyTests(unittest.TestCase):
    def setUp(self):
        self.setup = economy_fixture.small_setup(carriage_rates={"cart": 0.19, "road": 0.1})
        self.edge = road_between(economy_fixture.TOWN, economy_fixture.FARMS)
        self.pair = (economy_fixture.TOWN, economy_fixture.FARMS)

    def test_the_setup_carries_the_ways_into_its_carriage_table(self):
        built = dataclasses.replace(self.setup, improvements=self.edge)
        self.assertLess(built.carriage_table().cost_per_tonne(*self.pair),
                        self.setup.carriage_table().cost_per_tonne(*self.pair))

    def test_the_live_economy_rebuilds_its_carriage_table_when_a_way_is_finished(self):
        economy = economy_api.blank_economy(self.setup)
        before = economy.carriage.cost_per_tonne(*self.pair)
        self.assertTrue(economy_api.set_improvements(economy, self.edge))
        self.assertLess(economy.carriage.cost_per_tonne(*self.pair), before)
        self.assertFalse(economy_api.set_improvements(economy, self.edge))

    def test_the_spin_up_key_sees_the_ways(self):
        self.assertIn("improvements", {field.name for field in dataclasses.fields(EconomySetup)})
        built = dataclasses.replace(self.setup, improvements=self.edge)
        self.assertNotEqual(economy_port_key.setup_digest(self.setup), economy_port_key.setup_digest(built))


if __name__ == "__main__":
    unittest.main()
