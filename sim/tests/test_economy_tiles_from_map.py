"""How the economy's tiles read geography (sim/economy/tile_costs.py): `following_site` takes a tile's cropland and
fertility from a crop site, and `tiles_from_map` reads each tile's facts and crop site from the map it is given.
Stand-ins for the site and the map; no game."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import tile_costs
from sim.economy.types import HECTARES_PER_SQUARE_KILOMETRE, TileSpec

AREA_KM2 = 200.0
CROPPED_SHARE = 2.0 / 3.0
TILLAGE = 0.7


def tile():
    return TileSpec("a", 40.0, 10.0, AREA_KM2, False, ("b",), 0.0, 0.0)


class FollowingSiteTests(unittest.TestCase):
    def test_cropland_share_and_fertility_come_from_the_crop_site(self):
        site = types.SimpleNamespace(cropped_hectares=3000.0, yield_factor=1.3)
        followed = tile_costs.following_site(tile(), site)
        self.assertAlmostEqual(followed.cropped_fraction, 3000.0 / (AREA_KM2 * HECTARES_PER_SQUARE_KILOMETRE))
        self.assertEqual(followed.fertility, 1.3)

    def test_ground_that_yields_nothing_is_not_cropland(self):
        site = types.SimpleNamespace(cropped_hectares=3000.0, yield_factor=0.0)
        followed = tile_costs.following_site(tile(), site)
        self.assertEqual(followed.cropped_fraction, 0.0)
        self.assertEqual(followed.fertility, 0.0)

    def test_a_tile_of_no_area_has_no_cropped_share(self):
        flat = TileSpec("a", 40.0, 10.0, 0.0, False, (), 0.0, 0.0)
        site = types.SimpleNamespace(cropped_hectares=10.0, yield_factor=1.0)
        self.assertEqual(tile_costs.following_site(flat, site).cropped_fraction, 0.0)


class TilesFromMapTests(unittest.TestCase):
    FACTS = {"lat": 41.5, "lon": 12.25, "land_area_km2": AREA_KM2, "coastal": True, "neighbours": ["b", "c"],
             "climate_class": "Csa"}

    def read(self):
        world_map = object()
        crop_site = mock.Mock(return_value=types.SimpleNamespace(cropped_hectares=5000.0, yield_factor=0.9))
        tile_facts = mock.Mock(return_value=dict(self.FACTS))
        with mock.patch.object(tile_costs, "crop_site", crop_site), mock.patch.object(tile_costs, "tile_facts", tile_facts):
            tiles = tile_costs.tiles_from_map(world_map, ["a"], CROPPED_SHARE, TILLAGE)
        return world_map, tiles, crop_site, tile_facts

    def test_each_tiles_facts_and_site_are_read_from_the_map_given(self):
        world_map, _tiles, crop_site, tile_facts = self.read()
        tile_facts.assert_called_once_with("a", world_map)
        crop_site.assert_called_once_with("a", CROPPED_SHARE, world_map, tillage_capacity=TILLAGE)

    def test_the_tile_carries_the_maps_position_borders_and_climate(self):
        tiles = self.read()[1]
        self.assertEqual((tiles["a"].latitude, tiles["a"].longitude), (41.5, 12.25))
        self.assertEqual(tiles["a"].borders, ("b", "c"))
        self.assertTrue(tiles["a"].coastal)
        self.assertEqual(tiles["a"].climate_class, "Csa")

    def test_the_tiles_cropland_and_fertility_are_the_crop_sites(self):
        tile_spec = self.read()[1]["a"]
        self.assertAlmostEqual(tile_spec.cropland_hectares, 5000.0)
        self.assertEqual(tile_spec.fertility, 0.9)


if __name__ == "__main__":
    unittest.main()
