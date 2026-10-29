"""The land module's views of places on the map (sim/land/map_places.py): a tile's record, the land area of tiles, the climate of
tiles, the names and regions on them and the endemic disease of the ground. Each is called on a land module over a small map of
two tiles written out here, or the base map where the answer needs its data; no game."""
QUICK_TOPIC = True

import types
import unittest

from sim.geography import api as geography
from sim.tests import land_host, resources_stand_in

SMALL_MAP = geography.map_of_tiles({
    "a": {"lat": 12.5, "lon": 3.25, "land_area_km2": 200.0, "coastal": True, "borders": ["b"]},
    "b": {"lat": 13.5, "lon": 3.25, "land_area_km2": 100.5, "coastal": False, "borders": ["a"]}})
ROME = {"id": "rome", "home_tiles": ["a", "b"]}


def small_land():
    module = land_host.build(ROME)
    module._map_cache = SMALL_MAP
    return module


class TileDescriptionTests(unittest.TestCase):
    def test_a_tile_is_described_by_the_map_it_is_on(self):
        described = small_land().tile_description("a")
        self.assertEqual((described["lat"], described["lon"], described["land_area_km2"]), (12.5, 3.25, 200.0))
        self.assertEqual((described["coastal"], described["neighbours"]), (True, ["b"]))


class LandAreaTests(unittest.TestCase):
    def test_the_land_area_of_tiles_is_the_sum_of_their_areas(self):
        self.assertEqual(small_land().land_area_of(["a", "b"]), 300.5)

    def test_no_tiles_have_no_land(self):
        self.assertEqual(small_land().land_area_of([]), 0.0)


class TileClimatesTests(unittest.TestCase):
    def test_each_tile_gives_its_latitude_and_climate_layers_in_the_order_asked(self):
        climates = small_land().tile_climates(["b", "a"])
        self.assertEqual([climate["lat"] for climate in climates], [13.5, 12.5])
        self.assertEqual(set(climates[0]), {"lat", "koppen_class", "koppen_sample_mix"})


class TilePlacesTests(unittest.TestCase):
    def test_the_places_the_map_puts_on_a_tile_come_highest_rank_first(self):
        places = [{"id": "x", "name": "Small", "tile": "a", "rank": 1}, {"id": "y", "name": "Great", "tile": "a", "rank": 9},
                  {"id": "z", "name": "Elsewhere", "tile": "b"}]
        module = small_land()
        module._map_cache = types.SimpleNamespace(
            catalogue=lambda name: {entry["id"]: entry for entry in places} if name == "places" else {})
        self.assertEqual(module.tile_places("a"), ["Great", "Small"])
        self.assertEqual(module.tile_places("c"), [])


class RegionsAndDiseaseTests(unittest.TestCase):
    def test_the_regions_of_romes_tiles_include_italia_and_are_sorted(self):
        module = land_host.build(resources_stand_in.rome())
        regions = module.regions_of(module.tiles_listed_by(resources_stand_in.rome()))
        self.assertIn("italia", regions)
        self.assertEqual(regions, sorted(regions))

    def test_the_ground_romes_people_live_on_takes_working_age_people_each_year(self):
        module = land_host.build(resources_stand_in.rome())
        loss = module.endemic_people_loss(module.tiles_listed_by(resources_stand_in.rome()))
        self.assertGreater(loss["working_age"], 0.0)


if __name__ == "__main__":
    unittest.main()
