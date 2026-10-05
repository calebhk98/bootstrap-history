"""Complaint 328: a region's anchor point is derived from its tiles, never
hand-set in geography.json."""
import json
import math
import os
import unittest

from sim.geography.api import load_geography

from sim.geography import regions

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _geography():
    return load_geography()


def _unit(latitude, longitude):
    lat, lon = math.radians(latitude), math.radians(longitude)
    return (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat))


class RegionAnchorTests(unittest.TestCase):

    def test_no_region_record_carries_its_own_position(self):
        for region_id, record in _geography()["regions"].items():
            if region_id.startswith("_"):
                continue
            self.assertNotIn("lat", record, region_id)
            self.assertNotIn("lon", record, region_id)

    def test_anchor_is_the_area_weighted_centre_of_the_tiles(self):
        geography = _geography()
        tiles = geography["land_tiles"]["tiles"]
        view = regions.region_records(geography)
        for region_id, tile_ids in geography["land_tiles"]["region_to_tiles"].items():
            total = [0.0, 0.0, 0.0]
            for tile_id in tile_ids:
                weight = tiles[tile_id]["land_area_km2"]
                vector = _unit(tiles[tile_id]["lat"], tiles[tile_id]["lon"])
                total = [a + weight * b for a, b in zip(total, vector)]
            expected_lat = math.degrees(math.atan2(total[2], math.hypot(total[0], total[1])))
            expected_lon = math.degrees(math.atan2(total[1], total[0]))
            self.assertAlmostEqual(view[region_id]["lat"], expected_lat, places=6, msg=region_id)
            self.assertAlmostEqual(view[region_id]["lon"], expected_lon, places=6, msg=region_id)

    def test_anchor_follows_an_edited_tile(self):
        geography = _geography()
        before = regions.region_records(geography)["italia"]["lon"]
        tile_id = geography["land_tiles"]["region_to_tiles"]["italia"][0]
        geography["land_tiles"]["tiles"][tile_id]["lon"] += 20.0
        self.assertNotEqual(regions.region_records(geography)["italia"]["lon"], before)


if __name__ == "__main__":
    unittest.main()
