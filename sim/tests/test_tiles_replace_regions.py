"""Complaints/140: land area and mineral deposits read the tiles, not the regions.

A region is a label over tiles. These tests alter or remove the region-level
copy and require the answer not to move, so any reader that still goes
through the region layer fails here.
"""
import copy
import json
import os
import unittest

from sim.world import deposits

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _geography():
    with open(os.path.join(_ROOT, "data", "world", "geography.json")) as handle:
        return json.load(handle)


class DepositsReadTilesTests(unittest.TestCase):

    def test_every_deposit_sits_on_a_real_tile(self):
        tiles = _geography()["land_tiles"]["tiles"]
        for metal in deposits.METALS:
            for deposit in deposits.load_deposits(metal):
                self.assertIn(deposit.tile, tiles, "%s: %s" % (metal, deposit.name))

    def test_deposit_quantities_do_not_need_the_region_records(self):
        geography = _geography()
        stripped = copy.deepcopy(geography)
        stripped["regions"] = {}
        for metal in deposits.METALS:
            expected = [(d.name, d.quantity_tonnes_per_year)
                        for d in deposits.load_deposits(metal, geography)]
            actual = [(d.name, d.quantity_tonnes_per_year)
                      for d in deposits.load_deposits(metal, stripped)]
            self.assertEqual(expected, actual, metal)

    def test_a_tile_share_moves_the_deposit_that_sits_on_it(self):
        geography = _geography()
        base = {d.name: d.quantity_tonnes_per_year
                for d in deposits.load_deposits("tin", geography)}
        doubled = copy.deepcopy(geography)
        for deposit in deposits.load_deposits("tin", geography):
            tile_minerals = doubled["land_tiles"]["tiles"][deposit.tile]["minerals"]
            tile_minerals["tin"] *= 2.0
        for deposit in deposits.load_deposits("tin", doubled):
            self.assertAlmostEqual(deposit.quantity_tonnes_per_year,
                                   2.0 * base[deposit.name], places=9)


class MineralSharesAreNotDuplicatedTests(unittest.TestCase):

    def test_no_region_and_tile_both_carry_the_same_metal(self):
        geography = _geography()
        tiles = geography["land_tiles"]["tiles"]
        region_to_tiles = geography["land_tiles"]["region_to_tiles"]
        duplicated = []
        for region_id, region in geography["regions"].items():
            if region_id.startswith("_"):
                continue
            for metal, share in (region.get("minerals") or {}).items():
                if not share:
                    continue
                for tile_id in region_to_tiles.get(region_id, []):
                    if metal in (tiles[tile_id].get("minerals") or {}):
                        duplicated.append((region_id, metal, tile_id))
        self.assertEqual(duplicated, [])

    def test_regional_totals_still_sum_to_one_over_the_home_regions(self):
        from sim.world import mineral_shares
        geography = _geography()
        home = [region_id for region_id, region in geography["regions"].items()
                if not region_id.startswith("_") and region["reach_from_italia"] <= 1]
        regional = mineral_shares.regional_mineral_shares(geography)
        for metal in ("iron", "copper", "tin", "lead", "silver"):
            total = sum(regional[region_id].get(metal, 0.0) for region_id in home)
            self.assertAlmostEqual(total, 1.0, delta=0.06, msg=metal)


class ForestAreaReadsTilesTests(unittest.TestCase):

    def test_home_land_area_is_the_sum_of_the_tiles(self):
        from sim.tests.harness import sim
        test_sim = sim(civ="rome_100ad")
        geography = _geography()
        tiles = geography["land_tiles"]["tiles"]
        expected = sum(tiles[tile_id]["land_area_km2"]
                       for region_id in test_sim.civ["home_regions"]
                       for tile_id in geography["land_tiles"]["region_to_tiles"][region_id])
        self.assertAlmostEqual(test_sim.home_land_area_km2(), expected, places=6)

    def test_home_land_area_ignores_the_region_record(self):
        from sim.tests.harness import sim
        test_sim = sim(civ="rome_100ad")
        before = test_sim.home_land_area_km2()
        for region in test_sim._regions.values():
            region["land"] = dict(region["land"], land_area_km2=1.0)
        self.assertEqual(test_sim.home_land_area_km2(), before)
