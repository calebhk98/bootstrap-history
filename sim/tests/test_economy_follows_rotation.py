"""Complaint 537: the economy's cropland and tile yields follow the farm's sites (the society's rotation and soil as they
become), not as the setup found them: `follow_farm_sites` on built tiles and sites."""
QUICK_TOPIC = True

import types
import unittest

from sim.economy.types import TileSpec
from sim.markets.port_cropland import follow_farm_sites
from sim.tests.ui_stand_in import Game

AREA_KM2 = 100.0
HECTARES = AREA_KM2 * 100.0


def tile(tile_id, cropped_fraction=0.2, fertility=1.0):
    return TileSpec(tile_id=tile_id, latitude=40.0, longitude=10.0, land_area_km2=AREA_KM2, coastal=False, borders=(),
                    cropped_fraction=cropped_fraction, fertility=fertility)


def site(cropped_hectares, yield_factor):
    return types.SimpleNamespace(cropped_hectares=cropped_hectares, yield_factor=yield_factor)


def setup_of(*tiles):
    return types.SimpleNamespace(tiles={held.tile_id: held for held in tiles},
                                 yield_factor_by_recipe_tile={"wheat@%s" % held.tile_id: held.fertility for held in tiles})


def game_with(sites):
    return Game(farm_sites=lambda: sites)


class FollowFarmSites(unittest.TestCase):
    def test_a_rotation_that_crops_more_ground_reaches_the_economys_cropland(self):
        setup = setup_of(tile("a", cropped_fraction=0.2))
        follow_farm_sites(game_with({"a": site(0.2 * HECTARES, 1.0)}), setup)
        self.assertAlmostEqual(setup.tiles["a"].cropland_hectares, 0.2 * HECTARES)
        follow_farm_sites(game_with({"a": site(0.3 * HECTARES, 1.0)}), setup)
        self.assertAlmostEqual(setup.tiles["a"].cropland_hectares, 0.3 * HECTARES)

    def test_worn_soil_lowers_the_tiles_yield_and_every_recipe_yield_keyed_to_it(self):
        setup = setup_of(tile("a"), tile("b"))
        setup.yield_factor_by_recipe_tile["barley@a"] = 1.0
        follow_farm_sites(game_with({"a": site(0.2 * HECTARES, 0.7), "b": site(0.2 * HECTARES, 1.0)}), setup)
        self.assertEqual(setup.tiles["a"].fertility, 0.7)
        self.assertEqual(setup.yield_factor_by_recipe_tile["wheat@a"], 0.7)
        self.assertEqual(setup.yield_factor_by_recipe_tile["barley@a"], 0.7)
        self.assertEqual(setup.yield_factor_by_recipe_tile["wheat@b"], 1.0)

    def test_ground_that_yields_nothing_is_not_cropland(self):
        setup = setup_of(tile("a"))
        follow_farm_sites(game_with({"a": site(0.2 * HECTARES, 0.0)}), setup)
        self.assertEqual(setup.tiles["a"].cropland_hectares, 0.0)

    def test_a_site_off_the_setup_is_ignored_and_an_unchanged_site_moves_nothing(self):
        setup = setup_of(tile("a"))
        before = dict(setup.tiles)
        follow_farm_sites(game_with({"a": site(0.2 * HECTARES, 1.0), "elsewhere": site(5.0, 1.0)}), setup)
        self.assertEqual(setup.tiles, before)


if __name__ == "__main__":
    unittest.main()
