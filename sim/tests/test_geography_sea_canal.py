"""Complaint 601: a canal across an isthmus joins two seas as a way. The map's `isthmuses` catalogue says where a
cut is physically possible (length, mean ground height, bank slope); the cost is the earth moved at the canal
mode's labour rates, and a built cut is a sea link the route search uses."""
QUICK_TOPIC = True

import unittest

from sim.geography import api
from sim.geography.map_source import WorldMap

HELD = {"sea_square_sail"}
WAY = "sea_canal"
SITE_TILES = ("greece_01", "turkey_01")  # joined by an ordinary sea link of several hundred km


def _with_cut(world_map, cut_id, tile_a, tile_b, length_km, height_m=20.0):
    cut = {"id": cut_id, "way": WAY, "tile_a": tile_a, "tile_b": tile_b, "length_km": length_km,
           "mean_ground_height_m": height_m, "side_slope_run_per_rise": 0.5, "builds_like": "canal"}
    catalogues = dict(world_map.catalogues)
    catalogues["isthmuses"] = {cut_id: cut}
    return WorldMap(world_map.map_id, world_map.tiles, world_map.layers, catalogues, world_map.folders, world_map.properties)


def _sail(world_map, origin, destination, built):
    return api.route([origin], [destination], {"sail"}, improvements=built, world_map=world_map, held_nodes=HELD)


class SeaCanalTests(unittest.TestCase):

    def setUp(self):
        self.base = api.open_map()
        self.map = _with_cut(self.base, "test_cut", *SITE_TILES, length_km=60.0)
        self.key = api.edge_key(*SITE_TILES)

    def test_a_declared_isthmus_can_be_built_and_names_its_physical_work(self):
        needs = api.build_requirements(*SITE_TILES, WAY, world_map=self.map)
        self.assertIsNotNone(needs)
        self.assertGreater(needs["labour_hours"], 0.0)
        self.assertAlmostEqual(needs["km"], 60.0)
        self.assertGreater(needs["build_years"], 0.0)

    def test_no_isthmus_declared_means_no_canal(self):
        self.assertIsNone(api.build_requirements("greece_01", "greece_02", WAY, world_map=self.map))
        self.assertIsNone(api.build_requirements(*SITE_TILES, WAY, world_map=self.base))

    def test_the_cost_grows_with_the_length_of_the_cut(self):
        short = api.build_requirements(*SITE_TILES, WAY, world_map=_with_cut(self.base, "cut", *SITE_TILES, length_km=30.0))
        long = api.build_requirements(*SITE_TILES, WAY, world_map=_with_cut(self.base, "cut", *SITE_TILES, length_km=90.0))
        self.assertAlmostEqual(long["labour_hours"] / short["labour_hours"], 3.0, places=6)
        self.assertGreater(long["build_years"], short["build_years"])

    def test_the_cost_grows_with_the_height_of_ground_cut_through(self):
        low = api.build_requirements(*SITE_TILES, WAY, world_map=_with_cut(self.base, "cut", *SITE_TILES, 60.0, 5.0))
        high = api.build_requirements(*SITE_TILES, WAY, world_map=_with_cut(self.base, "cut", *SITE_TILES, 60.0, 60.0))
        self.assertGreater(high["labour_hours"], 2.0 * low["labour_hours"])

    def test_a_built_canal_shortens_the_sea_route_in_days_and_freight(self):
        before = _sail(self.map, *SITE_TILES, {})
        after = _sail(self.map, *SITE_TILES, {self.key: {WAY: True}})
        self.assertIsNotNone(before)
        self.assertLess(after["legs"][0]["km"], before["legs"][0]["km"])
        self.assertLess(after["days"], before["days"])
        self.assertLess(after["cost_per_tonne"], before["cost_per_tonne"])

    def test_an_unbuilt_cut_changes_no_route(self):
        self.assertEqual(_sail(self.map, *SITE_TILES, {}), _sail(self.base, *SITE_TILES, {}))

    def test_the_suez_isthmus_joins_two_seas_that_had_no_sea_route(self):
        tiles = ("egypt_08", "egypt_06")
        self.assertIsNone(_sail(self.base, *tiles, {}))
        built = {api.edge_key(*tiles): {WAY: True}}
        self.assertIsNotNone(_sail(self.base, *tiles, built))

    def test_built_kilometres_count_the_cut(self):
        self.assertAlmostEqual(api.built_km({self.key: {WAY: True}}, WAY, world_map=self.map), 60.0)

    def test_the_catalogue_is_sound(self):
        self.assertEqual([problem for problem in api.problems() if "isthmus" in problem], [])


if __name__ == "__main__":
    unittest.main()
