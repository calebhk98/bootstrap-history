"""Tile fertility and region fertility are one scale: a tile's fertility is
that of its arable ground, and a region's is derived from its tiles."""
from sim.geography.api import load_geography
import copy
import json
import os
import sys
import unittest

from sim.world import land

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_ROOT, "tools"))
import generate_geography_tiles as generator  # noqa: E402

_GEOGRAPHY = load_geography()
_TILES = _GEOGRAPHY["land_tiles"]["tiles"]
_REGION_TO_TILES = _GEOGRAPHY["land_tiles"]["region_to_tiles"]


class TileFertilityIsOfArableGroundTests(unittest.TestCase):
    def test_every_tile_matches_the_generator_rule_applied_to_its_climate_mix(self):
        for tile_id, tile in _TILES.items():
            arable, fertility = generator.arable_and_fertility_from_mix(tile["koppen_sample_mix"])
            self.assertAlmostEqual(tile["arable_fraction"], arable, delta=1e-4, msg=tile_id)
            self.assertAlmostEqual(tile["fertility_quality_multiplier"], fertility,
                                   delta=1e-4, msg=tile_id)

    def test_a_mixed_tile_is_weighted_by_arable_share_not_by_area(self):
        # Mostly tundra by area, but the arable ground is Mediterranean.
        arable, fertility = generator.arable_and_fertility_from_mix({"ET": 20, "Csa": 5})
        self.assertGreater(fertility, 0.9)
        self.assertLess(arable, 0.1)

    def test_reference_class_defines_the_reference_scale(self):
        self.assertEqual(generator.KOPPEN_ARABLE_AND_FERTILITY["Csa"][1], 1.0)
        _arable, fertility = generator.arable_and_fertility_from_mix({"Csa": 25})
        self.assertAlmostEqual(fertility, 1.0)

    def test_italia_arable_ground_sits_near_the_reference(self):
        lands = land.load_region_lands()
        self.assertAlmostEqual(lands["italia"].fertility_quality_multiplier, 1.0, delta=0.05)


class RegionFertilityIsDerivedTests(unittest.TestCase):
    def test_no_shipped_region_stores_its_own_fertility(self):
        for region, record in _GEOGRAPHY["regions"].items():
            if region.startswith("_"):
                continue
            self.assertNotIn("fertility_quality_multiplier", record.get("land", {}), region)

    def test_region_fertility_is_the_arable_weighted_mean_of_its_tiles(self):
        lands = land.load_region_lands()
        for region, tile_ids in _REGION_TO_TILES.items():
            arable = sum(_TILES[t]["land_area_km2"] * _TILES[t]["arable_fraction"] for t in tile_ids)
            weighted = sum(_TILES[t]["land_area_km2"] * _TILES[t]["arable_fraction"]
                           * _TILES[t]["fertility_quality_multiplier"] for t in tile_ids)
            if arable > 0:
                self.assertAlmostEqual(lands[region].fertility_quality_multiplier,
                                       weighted / arable, places=9, msg=region)

    def test_region_without_tiles_has_no_land(self):
        geography = copy.deepcopy(_GEOGRAPHY)
        geography["regions"]["orphan"] = copy.deepcopy(geography["regions"]["italia"])
        self.assertNotIn("orphan", land.load_region_lands(geography))


if __name__ == "__main__":
    unittest.main()
