"""Complaints/136: mineral access and located materials are read per tile; a region record is a label.

Geography is opened on the real map and deposit catalogue with a small stand-in for the engine, so no game is built.
"""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.constants import REGISTRY
from sim.geography import api, map_source, reach_bands
from sim.geography.geography import Geography
from sim.geography.api import mineral_shares

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRACKED = {"iron", "coal", "copper", "lead", "tin", "silver", "saltpetre"}


def _civilisation(civilisation_id):
    with open(os.path.join(_ROOT, "data", "civilizations", civilisation_id + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


class _World:
    """The parts of the engine that Geography reads."""

    pop_scale = 1.0

    def __init__(self, civilisation, held_nodes=()):
        self.civ = civilisation
        self.held_nodes = set(held_nodes)
        self.improvements = {}
        self.world_map = map_source.load_map()

    def civilisation(self, civilisation_id):
        return _civilisation(civilisation_id)


def _geography(civilisation):
    geography = Geography(_World(civilisation, civilisation.get("starting_techs") or ()))
    geography.open(api.load_geography())
    return geography


class RegionRecordsCarryNoMineralsTests(unittest.TestCase):

    def test_a_region_record_has_only_its_label_fields(self):
        for region_id, record in api.load_geography()["regions"].items():
            if not region_id.startswith("_"):
                self.assertLessEqual(set(record), {"name", "note"}, region_id)

    def test_geographys_region_view_has_no_mineral_table(self):
        for region_id, record in _geography(_civilisation("rome_100ad")).regions.items():
            self.assertNotIn("minerals", record, region_id)

    def test_no_located_material_names_a_region(self):
        for material_id, entry in api.load_geography()["located_materials"].items():
            if not material_id.startswith("_"):
                self.assertNotIn("regions", entry, material_id)
                self.assertTrue(entry.get("places"), material_id)


class EveryShareHasASourceTests(unittest.TestCase):

    def test_the_seven_minerals_are_tracked_by_deposits_and_gold_and_mercury_are_not(self):
        self.assertEqual(mineral_shares.tracked_resources(), TRACKED)

    def test_every_reference_share_row_names_a_source_and_is_declared_a_heuristic(self):
        rows = [row for row in mineral_shares.share_rows() if "share_of_reference_output" in row]
        self.assertGreater(len(rows), 40)
        for row in rows:
            self.assertTrue(row.get("source"), row["id"])
            self.assertIn(row.get("conf"), ("A", "B", "C", "D"), row["id"])
            declared = REGISTRY["DEPOSIT_REFERENCE_SHARE_%s" % row["id"].upper()]
            self.assertEqual(declared["kind"], "temporary_heuristic", row["id"])

    def test_every_tracked_resource_has_a_deposit_outside_the_roman_tiles(self):
        geography = api.load_geography()
        roman = set(api.tiles_held(_civilisation("rome_100ad")))
        by_tile = mineral_shares.deposit_shares_by_tile(geography)
        for resource in TRACKED:
            self.assertTrue(set(by_tile[resource]) - roman, resource)

    def test_the_reference_empires_shares_still_sum_to_one_for_each_metal(self):
        geography = api.load_geography()
        roman = api.tiles_held(_civilisation("rome_100ad"))
        for metal in ("iron", "copper", "tin", "lead", "silver"):
            self.assertAlmostEqual(mineral_shares.held_share(roman, metal, geography), 1.0, delta=0.1, msg=metal)

    def test_every_located_place_resolves_to_a_tile(self):
        geography = _geography(_civilisation("rome_100ad"))
        for material_id, tile_ids in geography._material_tiles.items():
            self.assertTrue(tile_ids, material_id)
            for tile_id in tile_ids:
                self.assertIn(tile_id, geography.data["land_tiles"]["tiles"], material_id)


class MineralScaleReadsTheDepositsTileTests(unittest.TestCase):

    def test_holding_the_tile_of_a_coalfield_draws_its_share_in_full(self):
        civilisation = dict(_civilisation("mexica_1500"))
        geography = _geography(civilisation)
        far = geography.mineral_scale("coal")
        ordos = max(mineral_shares.deposit_shares_by_tile(geography.data)["coal"].items(), key=lambda item: item[1])
        civilisation["home_tiles"] = [ordos[0]]
        held = _geography(civilisation)
        self.assertGreaterEqual(held.mineral_scale("coal"), ordos[1])
        self.assertGreater(held.mineral_scale("coal"), far)

    def test_the_scale_is_the_deposit_shares_faded_by_the_reach_of_their_tiles(self):
        geography = _geography(_civilisation("han_china_100ad"))
        for material in TRACKED:
            expected = sum(share * Geography.TRADE_ACCESS_BY_REACH.get(geography.tile_reach(tile_id), 0.02)
                           for tile_id, share in mineral_shares.deposit_shares_by_tile(geography.data)[material].items())
            self.assertAlmostEqual(geography.mineral_scale(material), max(0.05, expected), places=9, msg=material)

    def test_a_deposit_moved_to_another_tile_moves_the_scale(self):
        civilisation = _civilisation("rome_100ad")
        geography = _geography(civilisation)
        before = geography.mineral_scale("saltpetre")
        saltpetre_tiles = geography.source_tiles("saltpetre")
        civilisation = dict(civilisation, home_tiles=list(saltpetre_tiles))
        self.assertGreater(_geography(civilisation).mineral_scale("saltpetre"), before)

    def test_freight_sources_are_the_tiles_of_the_deposits(self):
        geography = _geography(_civilisation("mexica_1500"))
        self.assertEqual(set(geography.source_tiles("coal")),
                         set(mineral_shares.deposit_shares_by_tile(geography.data)["coal"]))
        self.assertIsNone(geography.route_km_to(()))
        self.assertGreater(geography.route_km_to(geography.source_tiles("coal")), 0.0)
        rome = _geography(_civilisation("rome_100ad"))
        self.assertEqual(rome.route_km_to(rome.source_tiles("coal")), 0.0)


class TileReachTests(unittest.TestCase):

    def test_a_held_tile_is_reach_zero_and_one_no_route_joins_is_the_farthest(self):
        civilisation = _civilisation("mexica_1500")
        geography = _geography(civilisation)
        for tile_id in api.tiles_held(civilisation):
            self.assertEqual(geography.tile_reach(tile_id), 0)
        self.assertEqual(geography.tile_reach("no_such_tile"), reach_bands.farthest_level(geography._world.world_map))

    def test_a_region_level_is_the_nearest_of_its_tiles(self):
        geography = _geography(_civilisation("rome_100ad"))
        for region_id in geography.regions:
            nearest = min(geography.tile_reach(tile_id)
                          for tile_id in geography.data["land_tiles"]["region_to_tiles"][region_id])
            self.assertEqual(geography.region_reach(region_id), nearest, region_id)


class LocatedMaterialsReadTileReachTests(unittest.TestCase):

    def test_a_material_costs_nothing_extra_where_the_tile_of_a_place_is_held(self):
        for civilisation_id in ("rome_100ad", "han_china_100ad", "mexica_1500"):
            geography = _geography(_civilisation(civilisation_id))
            for material_id, tile_ids in geography._material_tiles.items():
                reach, multiplier = geography.material_reach(material_id)
                if any(geography.tile_reach(tile_id) == 0 for tile_id in tile_ids):
                    self.assertEqual((reach, multiplier), (0, 1.0), (civilisation_id, material_id))
                else:
                    self.assertGreaterEqual(multiplier, 1.0, (civilisation_id, material_id))

    def test_holding_a_place_makes_the_material_home_ground(self):
        civilisation = _civilisation("rome_100ad")
        geography = _geography(civilisation)
        self.assertGreater(geography.material_reach("silk_raw")[0], 0)
        silk_tile = geography._material_tiles["silk_raw"][0]
        held = _geography(dict(civilisation, home_tiles=[silk_tile]))
        self.assertEqual(held.material_reach("silk_raw"), (0, 1.0))

    def test_a_place_is_reached_by_its_own_tile_not_by_its_old_region(self):
        civilisation = _civilisation("rome_100ad")
        geography = _geography(civilisation)
        tile_id = geography._material_tiles["silk_raw"][0]
        region_tiles = [tile for tile in geography.data["land_tiles"]["region_to_tiles"]["china"] if tile != tile_id]
        other = _geography(dict(civilisation, home_tiles=region_tiles[:1]))
        self.assertGreater(other.material_reach("silk_raw")[0], 0)


if __name__ == "__main__":
    unittest.main()
