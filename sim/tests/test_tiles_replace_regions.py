"""Complaints/136: land area and mineral deposits read the tiles, not the regions.

A region is a label over tiles. These tests alter or remove the region-level
copy and require the answer not to move, so any reader that still goes
through the region layer fails here.
"""
import json
import os
import unittest

from sim.geography.api import load_geography, regions_of_tiles, tiles_held

from sim.world import deposits

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _geography():
    return load_geography()


class DepositsReadTilesTests(unittest.TestCase):

    def test_every_deposit_sits_on_a_real_tile(self):
        tiles = _geography()["land_tiles"]["tiles"]
        for metal in deposits.METALS:
            for deposit in deposits.load_deposits(metal):
                self.assertIn(deposit.tile, tiles, "%s: %s" % (metal, deposit.name))

    def test_deposit_quantity_is_its_share_of_the_metal_total(self):
        resources = deposits._load_json(deposits.RESOURCES_FILE)
        deposits_data = deposits.load_deposit_data()
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

    def test_no_region_record_stores_a_share_of_output(self):
        for region_id, region in _geography()["regions"].items():
            if not region_id.startswith("_"):
                self.assertNotIn("minerals", region, region_id)

    def test_a_deposit_stores_its_share_once(self):
        both = [row["id"] for row in deposits.deposit_records()
                if "share_of_empire_output" in row and "share_of_reference_output" in row]
        self.assertEqual(both, [])

    def test_the_reference_empires_shares_still_sum_to_one_over_its_tiles(self):
        from sim.geography.api import mineral_shares
        geography = _geography()
        with open(os.path.join(_ROOT, "data", "civilizations", "rome_100ad.json"), encoding="utf-8") as handle:
            held = tiles_held(json.load(handle))
        for metal in ("iron", "copper", "tin", "lead", "silver"):
            self.assertAlmostEqual(mineral_shares.held_share(held, metal, geography), 1.0, delta=0.1, msg=metal)


class RegionRecordsHoldNoTileDataTests(unittest.TestCase):

    LABEL_FIELDS = {"name", "note"}

    def test_a_region_record_is_only_a_label(self):
        extra = {region_id: sorted(set(region) - self.LABEL_FIELDS)
                 for region_id, region in _geography()["regions"].items()
                 if not region_id.startswith("_") and set(region) - self.LABEL_FIELDS}
        self.assertEqual(extra, {})

    def test_no_region_field_repeats_a_tile_layer(self):
        from sim.geography import api
        layers = set(api.open_map().layers) | {"lat", "lon", "coastal", "land_area_km2", "borders"}
        for region_id, region in _geography()["regions"].items():
            if not region_id.startswith("_"):
                self.assertEqual(set(region) & layers, set(), region_id)


class ForestAreaReadsTilesTests(unittest.TestCase):

    def test_home_land_area_is_the_sum_of_the_tiles(self):
        from sim.tests.harness import sim
        test_sim = sim(civ="rome_100ad")
        geography = _geography()
        tiles = geography["land_tiles"]["tiles"]
        from sim.geography.api import tiles_held
        expected = sum(tiles[tile_id]["land_area_km2"] for tile_id in tiles_held(test_sim.civ))
        self.assertAlmostEqual(test_sim.home_land_area_km2(), expected, places=6)

    def test_region_records_hold_no_land_figures(self):
        from sim.tests.harness import sim
        test_sim = sim(civ="rome_100ad")
        for region in test_sim.geography.regions.values():
            self.assertNotIn("land", region)


class NoModuleReadsRegionLabelsForTileDataTests(unittest.TestCase):
    """Farm land, weather cells, crop climate and the cast hold tiles: a civilisation that lists
    `home_tiles` and no labels gets the same farm land, weather cells, climate and place."""

    def _civilisation(self, region_labels_removed):
        import copy
        from sim.engine.data import load_civ
        civilisation = copy.deepcopy(load_civ("rome_100ad"))
        if not region_labels_removed:
            from sim.geography.api import regions_of_tiles
            civilisation["home_regions"] = regions_of_tiles(civilisation.pop("home_tiles"))
        return civilisation

    def test_farm_land_and_weather_cells_follow_the_tiles_held(self):
        from sim.tests.harness import sim
        labelled = sim(civ="rome_100ad")
        tiled = sim(civ="rome_100ad")
        tiled.civ = self._civilisation(True)
        territory = tiled._compute_farm_weather_cells()
        self.assertEqual([cell.cell_id for cell in territory],
                         [cell.cell_id for cell in labelled._compute_farm_weather_cells()])
        from sim.world import land
        self.assertEqual(land.territory_farmland(tiled_tiles(tiled.civ)).arable_hectares,
                         land.territory_farmland(tiled_tiles(labelled.civ)).arable_hectares)

    def test_crop_climate_and_cast_place_follow_the_tiles_held(self):
        from sim.agents.cast import profile_from_civilisation
        from sim.geography.api import crop_climate, tiles_held
        labelled, tiled = self._civilisation(False), self._civilisation(True)
        self.assertEqual(crop_climate.territory_classes(tiles_held(labelled)),
                         crop_climate.territory_classes(tiles_held(tiled)))
        self.assertEqual(profile_from_civilisation(labelled).location, profile_from_civilisation(tiled).location)
        self.assertIn(profile_from_civilisation(tiled).location, tiled["home_tiles"])


def tiled_tiles(civilisation):
    from sim.geography.api import tiles_held
    return tiles_held(civilisation)
