"""Complaints/136, 281, 282: a region is a label over tiles, and a deposit is
placed by position, not by a tile id that a regenerated grid would drop.
"""
import copy
import json
import os
import unittest

from sim.world import deposits, land, mineral_shares, regions, tile_lookup

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _geography():
    with open(os.path.join(_ROOT, "data", "world", "geography.json")) as handle:
        return json.load(handle)


def _real_regions(geography):
    return {region_id: record for region_id, record in geography["regions"].items()
            if not region_id.startswith("_")}


class RegionRecordsHoldNoLandNumbersTests(unittest.TestCase):

    def test_no_region_record_carries_a_land_block(self):
        for region_id, record in _real_regions(_geography()).items():
            self.assertNotIn("land", record, region_id)

    def test_every_region_has_tiles(self):
        geography = _geography()
        region_to_tiles = geography["land_tiles"]["region_to_tiles"]
        for region_id in _real_regions(geography):
            self.assertTrue(region_to_tiles.get(region_id), region_id)

    def test_region_land_is_the_sum_of_its_tiles(self):
        geography = _geography()
        tiles = geography["land_tiles"]["tiles"]
        lands = land.load_region_lands(geography)
        for region_id, tile_ids in geography["land_tiles"]["region_to_tiles"].items():
            area = sum(tiles[tile_id]["land_area_km2"] for tile_id in tile_ids)
            arable = sum(tiles[tile_id]["land_area_km2"] * tiles[tile_id]["arable_fraction"]
                         for tile_id in tile_ids)
            self.assertAlmostEqual(lands[region_id].land_area_km2, area, places=6, msg=region_id)
            self.assertAlmostEqual(lands[region_id].arable_hectares, arable * 100.0,
                                   places=4, msg=region_id)

    def test_region_land_follows_an_edited_tile(self):
        geography = copy.deepcopy(_geography())
        tile_id = geography["land_tiles"]["region_to_tiles"]["italia"][0]
        before = land.load_region_lands(geography)["italia"].land_area_km2
        geography["land_tiles"]["tiles"][tile_id]["land_area_km2"] += 1000.0
        after = land.load_region_lands(geography)["italia"].land_area_km2
        self.assertAlmostEqual(after - before, 1000.0, places=6)

    def test_region_with_no_tiles_has_no_land(self):
        geography = copy.deepcopy(_geography())
        geography["regions"]["orphan"] = copy.deepcopy(geography["regions"]["italia"])
        self.assertNotIn("orphan", land.load_region_lands(geography))


class RegionViewTests(unittest.TestCase):

    def test_view_adds_mineral_shares_to_every_label(self):
        geography = _geography()
        view = regions.region_records(geography)
        self.assertEqual(set(view), set(_real_regions(geography)))
        shares = mineral_shares.regional_mineral_shares(geography)
        for region_id, record in view.items():
            self.assertEqual(record["minerals"], shares[region_id])
            self.assertEqual(record["name"], geography["regions"][region_id]["name"])

    def test_region_of_tile_inverts_region_to_tiles(self):
        geography = _geography()
        region_of_tile = regions.region_of_tile(geography)
        for region_id, tile_ids in geography["land_tiles"]["region_to_tiles"].items():
            for tile_id in tile_ids:
                self.assertEqual(region_of_tile[tile_id], region_id)


class DepositsArePlacedByPositionTests(unittest.TestCase):

    def test_no_deposit_names_a_tile_id(self):
        with open(deposits.DEPOSITS_FILE) as handle:
            data = json.load(handle)
        for metal, entries in data["deposits"].items():
            if metal.startswith("_"):
                continue
            for entry in entries:
                self.assertNotIn("tile", entry, entry["name"])
                self.assertIn("lat", entry, entry["name"])
                self.assertIn("lon", entry, entry["name"])

    def test_every_deposit_resolves_to_a_real_tile(self):
        tiles = _geography()["land_tiles"]["tiles"]
        for metal in deposits.METALS:
            for deposit in deposits.load_deposits(metal):
                self.assertIn(deposit.tile, tiles, deposit.name)

    def test_position_resolves_to_the_nearest_tile_centre(self):
        tiles = {"a": {"lat": 0.0, "lon": 0.0}, "b": {"lat": 0.0, "lon": 10.0},
                 "c": {"lat": 80.0, "lon": 175.0}}
        self.assertEqual(tile_lookup.nearest_tile_id(tiles, 1.0, 2.0), "a")
        self.assertEqual(tile_lookup.nearest_tile_id(tiles, -1.0, 8.0), "b")
        # across the antimeridian and near the pole
        self.assertEqual(tile_lookup.nearest_tile_id(tiles, 85.0, -170.0), "c")

    def test_deposit_follows_its_position_when_the_grid_is_renumbered(self):
        geography = _geography()
        original = geography["land_tiles"]["tiles"]
        renamed = {"renamed_%d" % index: tile
                   for index, tile in enumerate(reversed(list(original.values())))}
        with open(deposits.DEPOSITS_FILE) as handle:
            data = json.load(handle)
        for entries in data["deposits"].values():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                old_tile = tile_lookup.nearest_tile_id(original, entry["lat"], entry["lon"])
                new_tile = tile_lookup.nearest_tile_id(renamed, entry["lat"], entry["lon"])
                self.assertEqual(
                    (renamed[new_tile]["lat"], renamed[new_tile]["lon"]),
                    (original[old_tile]["lat"], original[old_tile]["lon"]), entry["name"])

    def test_regional_totals_use_the_position_resolved_tile(self):
        geography = _geography()
        with open(deposits.DEPOSITS_FILE) as handle:
            data = json.load(handle)
        tiles = geography["land_tiles"]["tiles"]
        other_tile = next(tile_id for tile_id in tiles if tiles[tile_id]["country_majority"] == "China")
        moved = copy.deepcopy(data)
        moved["deposits"]["iron"][0]["lat"] = tiles[other_tile]["lat"]
        moved["deposits"]["iron"][0]["lon"] = tiles[other_tile]["lon"]
        base = mineral_shares.regional_mineral_shares(geography, data)
        shifted = mineral_shares.regional_mineral_shares(geography, moved)
        self.assertNotEqual(base, shifted)


if __name__ == "__main__":
    unittest.main()
