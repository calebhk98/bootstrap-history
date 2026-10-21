"""SCENARIO (Complaint 537): in a real game the economy's cropland and tile yields follow the society's rotation and soil as
they become. The rule itself is in test_economy_follows_rotation.py."""
import unittest
from unittest import mock

from .harness import *  # noqa: F401,F403
from sim.engine import economy_port_cropland, economy_port_setup
from sim.geography.api import tiles_held
from sim.world import agriculture, land


def _cropland(setup):
    return sum(tile.cropland_hectares for tile in setup.tiles.values())


class EconomyFollowsRotationInAGame(unittest.TestCase):
    def test_a_rotation_adopted_later_reaches_the_economys_cropland(self):
        game = unopened_sim()
        setup = economy_port_setup.build_setup(game)
        before = _cropland(setup)
        economy_port_cropland.follow_farm_sites(game, setup)
        self.assertAlmostEqual(_cropland(setup), before, delta=before * 1e-9)     # nothing changed, nothing moves
        technique = game.labour.farming_technique()._replace(rotation=agriculture.THREE_FIELD)
        with mock.patch.object(game.labour, "farming_technique", return_value=technique):
            economy_port_cropland.follow_farm_sites(game, setup)
            ceiling = land.territory_cropland(game.farm_sites()).cropped_hectares
        self.assertGreater(_cropland(setup), before)
        self.assertAlmostEqual(_cropland(setup), ceiling, delta=ceiling * 1e-9)

    def test_worn_soil_lowers_the_economys_tile_yield(self):
        game = unopened_sim()
        setup = economy_port_setup.build_setup(game)
        tile_id = max(tiles_held(game.civ, game.world_map), key=lambda tile: setup.tiles[tile].fertility)
        before = setup.tiles[tile_id].fertility
        game.state.economy.soil_nitrogen = {tile_id: 0.3}
        economy_port_cropland.follow_farm_sites(game, setup)
        self.assertLess(setup.tiles[tile_id].fertility, before)
        keyed = [value for key, value in setup.yield_factor_by_recipe_tile.items() if key.endswith("@" + tile_id)]
        self.assertTrue(keyed)
        self.assertTrue(all(value == setup.tiles[tile_id].fertility for value in keyed))


if __name__ == "__main__":
    unittest.main()
