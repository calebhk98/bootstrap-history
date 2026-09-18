"""Regression tests for tools/generate_geography_tiles.py's OUTPUT (the
"land_tiles" section it writes into data/world/geography.json) and for its
own small, dependency-free helper functions.

WHAT THIS DOES NOT TEST. Re-running the generator itself needs network
access (Natural Earth's shapefiles) and three extra packages (shapely,
geopandas, kgcpy) this project's own test suite does not otherwise depend
on - see tools/generate_geography_tiles.py's own module docstring for the
reproduction instructions. This file therefore tests the COMMITTED OUTPUT
(same discipline data/world/geography.json's other consumers already get
tested against) and the pure id/mapping helpers that need neither network
nor those packages, not the geometry pipeline itself.

Like sim/tests/test_land.py's own docstring says of its sibling module:
these are ORDERINGS and STRUCTURAL PROPERTIES, not particular numbers -
the exact tile count or a fertility figure will shift a little if Natural
Earth or kgcpy's own data ever changes, and a test that pinned today's
exact numbers would break for the wrong reason the day someone re-runs the
generator in good faith.

NOT REGISTERED in sim/tests/__main__.py's TOPICS - out of this task's own
ownership (CLAUDE.md's ownership list explicitly reserves that file to
whoever else is managing topic registration). Run directly:
    python3 -m unittest sim.tests.test_geography_tiles -v
"""
import json
import os
import sys
import time
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO_ROOT, "tools"))

import generate_geography_tiles as tiles_module  # noqa: E402

GEOGRAPHY_PATH = os.path.join(_REPO_ROOT, "data", "world", "geography.json")


def _load_geography():
    with open(GEOGRAPHY_PATH) as handle:
        return json.load(handle)


class SlugifyTests(unittest.TestCase):

    def test_plain_ascii_name(self):
        self.assertEqual(tiles_module.slugify("Italy"), "italy")

    def test_spaces_become_underscores(self):
        self.assertEqual(tiles_module.slugify("United States of America"),
                         "united_states_of_america")

    def test_punctuation_collapses_rather_than_multiplying_underscores(self):
        # Non-ASCII letters are kept (Python's str.isalnum() accepts them,
        # and a JSON object key has no reason to be ASCII-only); only
        # punctuation like the apostrophe and the space collapse to single
        # underscores rather than one each.
        self.assertEqual(tiles_module.slugify("Côte d'Ivoire"), "côte_d_ivoire")

    def test_empty_input_never_produces_an_empty_id(self):
        self.assertEqual(tiles_module.slugify(""), "unknown")
        self.assertEqual(tiles_module.slugify("---"), "unknown")


class OldRegionMappingTests(unittest.TestCase):
    """old_region_for_tile() is used only for the migration report, never
    for a tile's own geometry or fertility - see the generator's own
    module docstring. These tests are about THAT function's own rule
    (a plain lookup, plus the one special case for Russia), not about
    whether the mapping is historically the "right" one.
    """

    def test_a_mapped_country_returns_its_old_region(self):
        self.assertEqual(tiles_module.old_region_for_tile("Italy", 12.0), "italia")

    def test_an_unmapped_country_returns_none_rather_than_guessing(self):
        self.assertIsNone(tiles_module.old_region_for_tile("Mongolia", 100.0))

    def test_russia_splits_on_the_urals_meridian(self):
        east = tiles_module.old_region_for_tile("Russia", 61.0)
        west = tiles_module.old_region_for_tile("Russia", 59.0)
        self.assertEqual(east, "siberia_urals")
        self.assertIsNone(west)

    def test_every_mapped_region_id_is_a_real_geography_json_region(self):
        geography = _load_geography()
        real_region_ids = set(geography["regions"].keys())
        for country, region_id in tiles_module.COUNTRY_TO_OLD_REGION.items():
            self.assertIn(region_id, real_region_ids,
                          "COUNTRY_TO_OLD_REGION[%r] = %r is not a region "
                          "data/world/geography.json actually has" % (country, region_id))


class GeneratedFileShapeTests(unittest.TestCase):
    """The task's own constraint: geography.json keeps its existing
    top-level shape (regions/reach_levels/located_materials), with
    land_tiles added ALONGSIDE it, not instead of it.
    """

    @classmethod
    def setUpClass(cls):
        cls.geography = _load_geography()

    def test_the_original_three_top_level_keys_are_still_there(self):
        for key in ("regions", "reach_levels", "located_materials"):
            self.assertIn(key, self.geography)

    def test_land_tiles_is_the_one_new_top_level_key(self):
        expected = {"_doc", "regions", "reach_levels", "located_materials", "land_tiles"}
        self.assertEqual(set(self.geography.keys()), expected)

    def test_every_one_of_the_21_hand_written_regions_still_has_its_own_land_block(self):
        # This script never touches `regions` - if this ever fails, something
        # else edited geography.json's own region data, not this file.
        real_regions = [r for r in self.geography["regions"] if not r.startswith("_")]
        self.assertEqual(len(real_regions), 21)
        for region_id in real_regions:
            self.assertIn("land", self.geography["regions"][region_id])


class TileStructureTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.geography = _load_geography()
        cls.land_tiles = cls.geography["land_tiles"]
        cls.tiles = cls.land_tiles["tiles"]

    def test_tile_count_matches_the_declared_count(self):
        self.assertEqual(len(self.tiles), self.land_tiles["tile_count"])

    def test_roughly_a_thousand_tiles_not_wildly_more_or_fewer(self):
        # "Roughly a thousand" per Complaints/46's own arithmetic
        # (149,000,000 km2 / 150,000). Loose bounds - this is a sanity
        # check on the RULE (grid size, land threshold, Antarctica drop),
        # not a pinned count.
        self.assertGreater(len(self.tiles), 700)
        self.assertLess(len(self.tiles), 2000)

    def test_every_tile_has_every_required_field(self):
        required = {"lat", "lon", "land_area_km2", "arable_fraction",
                    "fertility_quality_multiplier", "coastal", "borders",
                    "conf", "koppen_class", "country_majority", "old_region",
                    "source"}
        for tile_id, tile in self.tiles.items():
            missing = required - set(tile.keys())
            self.assertFalse(missing, "%s is missing %s" % (tile_id, missing))

    def test_land_area_is_positive_and_never_above_the_nominal_cell_size(self):
        nominal = self.land_tiles["target_tile_area_km2"]
        for tile_id, tile in self.tiles.items():
            self.assertGreater(tile["land_area_km2"], 0, tile_id)
            # A little slack for projection/clipping floating point, never
            # a real multiple of the nominal cell.
            self.assertLessEqual(tile["land_area_km2"], nominal * 1.01, tile_id)

    def test_arable_fraction_is_a_fraction(self):
        for tile_id, tile in self.tiles.items():
            self.assertGreaterEqual(tile["arable_fraction"], 0.0, tile_id)
            self.assertLessEqual(tile["arable_fraction"], 1.0, tile_id)

    def test_fertility_is_never_negative(self):
        for tile_id, tile in self.tiles.items():
            self.assertGreaterEqual(tile["fertility_quality_multiplier"], 0.0, tile_id)

    def test_centroid_is_a_real_lat_lon(self):
        for tile_id, tile in self.tiles.items():
            self.assertGreaterEqual(tile["lat"], -90.0, tile_id)
            self.assertLessEqual(tile["lat"], 90.0, tile_id)
            self.assertGreaterEqual(tile["lon"], -180.0, tile_id)
            self.assertLessEqual(tile["lon"], 180.0, tile_id)

    def test_no_tile_borders_itself(self):
        for tile_id, tile in self.tiles.items():
            self.assertNotIn(tile_id, tile["borders"], tile_id)

    def test_borders_are_symmetric(self):
        # If A lists B as a border, B must list A back - both are read off
        # the SAME grid-adjacency rule in the same direction, so a mismatch
        # would mean a real bug in that rule, not a judgement call.
        for tile_id, tile in self.tiles.items():
            for neighbour_id in tile["borders"]:
                self.assertIn(tile_id, self.tiles[neighbour_id]["borders"],
                              "%s borders %s but not vice versa" % (tile_id, neighbour_id))

    def test_antarctica_was_dropped(self):
        for tile_id, tile in self.tiles.items():
            self.assertNotEqual(tile["country_majority"], "Antarctica", tile_id)

    def test_old_region_is_either_none_or_a_real_region(self):
        real_region_ids = set(self.geography["regions"].keys())
        for tile_id, tile in self.tiles.items():
            if tile["old_region"] is not None:
                self.assertIn(tile["old_region"], real_region_ids, tile_id)

    def test_at_least_one_tile_is_coastal_and_at_least_one_is_not(self):
        # A trivial but real property: a world with only one or the other
        # would mean the coastal rule itself is broken, not a fact about
        # geography.
        coastal_count = sum(1 for t in self.tiles.values() if t["coastal"])
        inland_count = sum(1 for t in self.tiles.values() if not t["coastal"])
        self.assertGreater(coastal_count, 0)
        self.assertGreater(inland_count, 0)


class RegionToTilesMappingTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.geography = _load_geography()
        cls.land_tiles = cls.geography["land_tiles"]

    def test_every_mapped_tile_id_actually_exists(self):
        tiles = self.land_tiles["tiles"]
        for region_id, tile_ids in self.land_tiles["region_to_tiles"].items():
            for tile_id in tile_ids:
                self.assertIn(tile_id, tiles,
                              "%s lists %s, which is not a real tile" % (region_id, tile_id))

    def test_every_mapped_tile_actually_points_back_at_that_region(self):
        tiles = self.land_tiles["tiles"]
        for region_id, tile_ids in self.land_tiles["region_to_tiles"].items():
            for tile_id in tile_ids:
                self.assertEqual(tiles[tile_id]["old_region"], region_id)

    def test_rome_holds_dramatically_more_tiles_than_han_china(self):
        # THE ANCHOR CLAIM Complaints/46 is about: Rome's seven regions
        # should now visibly be a much bigger territory than China's one,
        # in TILE COUNT, not just in the old single land_area_km2 number.
        with open(os.path.join(_REPO_ROOT, "data", "civilizations", "rome_100ad.json")) as f:
            rome = json.load(f)
        with open(os.path.join(_REPO_ROOT, "data", "civilizations", "han_china_100ad.json")) as f:
            han = json.load(f)
        region_to_tiles = self.land_tiles["region_to_tiles"]
        rome_tile_count = sum(len(region_to_tiles.get(r, [])) for r in rome["home_regions"])
        han_tile_count = sum(len(region_to_tiles.get(r, [])) for r in han["home_regions"])
        self.assertGreater(rome_tile_count, han_tile_count)


class ItaliaAnchorTests(unittest.TestCase):
    """CLAUDE.md's own instruction for this task: italia's tiles must stay
    close to fertility 1.0, because data/production/40_organics.json's
    wheat_kg yield IS Roman-Italian dry-farmed wheat - the same anchor
    sim/world/land.py's own module docstring already states for the
    hand-written region. A LOOSE bound, not an exact match: italia's five
    tiles genuinely include non-Mediterranean terrain (the Alps) that one
    hand-written region-wide number averaged away - see the task's own
    report for the measured figure and why it is not exactly 1.0.
    """

    def test_italia_tiles_average_close_to_the_wheat_kg_anchor(self):
        geography = _load_geography()
        tiles = geography["land_tiles"]["tiles"]
        italia_tiles = [t for t in tiles.values() if t["old_region"] == "italia"]
        self.assertTrue(italia_tiles, "no tile mapped back to italia at all")
        total_area = sum(t["land_area_km2"] for t in italia_tiles)
        weighted_fertility = sum(
            t["fertility_quality_multiplier"] * t["land_area_km2"] for t in italia_tiles
        ) / total_area
        self.assertGreater(weighted_fertility, 0.7,
                           "italia's tiles drifted too far below the wheat_kg anchor")
        self.assertLessEqual(weighted_fertility, 1.05,
                             "italia's tiles should not exceed their own defining anchor")


class LandRentPerformanceTests(unittest.TestCase):
    """sim/world/land.py's own find_margin_of_cultivation(), UNCHANGED,
    called with the whole new tile set standing in for a civilization's
    territory - see tools/generate_geography_tiles.py's module docstring
    and this task's own report for the full before/after measurement. This
    is a guard against a future accidental quadratic regression, not a
    timing contract.
    """

    def test_whole_world_tile_scale_rent_computation_is_still_fast(self):
        from sim.world import land

        geography = _load_geography()
        tiles = geography["land_tiles"]["tiles"]
        region_lands = []
        for tile_id, tile in tiles.items():
            arable_km2 = tile["land_area_km2"] * tile["arable_fraction"]
            arable_iugera = arable_km2 * 100.0 / land.IUGERUM_HECTARES
            region_lands.append(land.RegionLand(
                region=tile_id, land_area_km2=tile["land_area_km2"],
                arable_fraction=tile["arable_fraction"],
                fertility_quality_multiplier=tile["fertility_quality_multiplier"],
                arable_iugera=arable_iugera))

        quantity_demanded = land.quantity_demanded_kg_grain_equivalent(65_000_000)
        start = time.perf_counter()
        land.find_margin_of_cultivation(region_lands, quantity_demanded)
        elapsed = time.perf_counter() - start
        # Measured around 1-2ms on this environment for ~1,100 tiles,
        # against sim/solve_prices.py's own ~370ms whole-solve budget
        # (Complaints/46). 250ms is a generous ceiling, not a tuned figure.
        self.assertLess(elapsed, 0.25,
                        "rent computation over the whole tile set took %.4fs" % elapsed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
