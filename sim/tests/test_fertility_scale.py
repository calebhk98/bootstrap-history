"""Tile fertility and region fertility are one scale: a tile's fertility is
that of its arable ground, and a region's is derived from its tiles."""

QUICK_TOPIC = True

from sim.geography.api import load_geography
import copy
import unittest

from sim.world import land

_GEOGRAPHY = load_geography()
_TILES = _GEOGRAPHY["land_tiles"]["tiles"]
_REGION_TO_TILES = _GEOGRAPHY["land_tiles"]["region_to_tiles"]


class TileFertilityIsOfArableGroundTests(unittest.TestCase):
    # The tile rule itself (derivation, reference class by class) is test_soil_derivation.
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
