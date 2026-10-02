"""Complaints/136: land area and mineral deposits read the tiles, not the regions.

A region is a label over tiles. These tests alter or remove the region-level
copy and require the answer not to move, so any reader that still goes
through the region layer fails here.
"""
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

    def test_deposit_quantity_is_its_share_of_the_metal_total(self):
        resources = deposits._load_json(deposits.RESOURCES_FILE)
        deposits_data = deposits._load_json(deposits.DEPOSITS_FILE)
        for metal in deposits.METALS:
            # the metal's own deposits split what is left after other metals' byproduct
            # recovery (silver riding with lead), so one ounce is counted once
            total = deposits.empire_output_net_of_byproducts_tonnes_per_year(
                metal, resources, deposits_data)
            shares = {entry["name"]: entry["share_of_empire_output"]
                      for entry in deposits_data["deposits"][metal]}
            for deposit in deposits.load_deposits(metal):
                self.assertAlmostEqual(deposit.quantity_tonnes_per_year,
                                       shares[deposit.name] * total, places=9)


class MineralSharesAreNotDuplicatedTests(unittest.TestCase):

    def test_a_deposit_share_is_not_also_in_its_region_table(self):
        geography = _geography()
        region_of_tile = {tile_id: region_id
                          for region_id, tile_ids in geography["land_tiles"]["region_to_tiles"].items()
                          for tile_id in tile_ids}
        duplicated = []
        for metal in deposits.METALS:
            for deposit in deposits.load_deposits(metal):
                region_id = region_of_tile.get(deposit.tile)
                listed = (geography["regions"].get(region_id, {}).get("minerals") or {}).get(metal)
                if listed:
                    duplicated.append((deposit.name, region_id, metal))
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

    def test_region_records_hold_no_land_figures(self):
        from sim.tests.harness import sim
        test_sim = sim(civ="rome_100ad")
        for region in test_sim._regions.values():
            self.assertNotIn("land", region)
