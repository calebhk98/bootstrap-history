"""Complaint 543: a tile's arable share, fertility and heavy-soil share come from its water balance, growing months and
ruggedness. Each rule is called on tiles of the built map. The old Koppen-keyed table is a reference the derived values
are validated against by class (CLAUDE.md 4.2), not an answer they must equal."""
QUICK_TOPIC = True

import statistics
import unittest
from collections import defaultdict

from sim.geography import soil_derivation, tile_layers
from sim.geography.api import open_map
from sim.tests.koppen_soil_reference import KOPPEN_ARABLE_AND_FERTILITY

MINIMUM_TILES_PER_CLASS = 5
CLASS_MEDIAN_ARABLE_TOLERANCE = 0.12
CLASS_MEDIAN_FERTILITY_TOLERANCE = 0.35
MEAN_ARABLE_ERROR_LIMIT = 0.06
MEAN_FERTILITY_ERROR_LIMIT = 0.20
ROUNDING = 1e-4   # the tile grid stores four decimals


class DerivedSoilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world_map = open_map()

    def tiles_of_class(self, koppen_class):
        return [tile_id for tile_id, record in sorted(self.world_map.tiles.items()) if record.get("koppen_class") == koppen_class]

    def median(self, koppen_class, rule):
        return statistics.median(rule(self.world_map, tile_id) for tile_id in self.tiles_of_class(koppen_class))

    def test_the_stored_tile_values_are_the_derivation(self):
        # A change to the rule or soil.json must be followed by `tools/generate_geography_tiles.py --rederive`.
        for tile_id, record in self.world_map.tiles.items():
            self.assertAlmostEqual(record["arable_fraction"], soil_derivation.arable_fraction(self.world_map, tile_id), delta=ROUNDING, msg=tile_id)
            self.assertAlmostEqual(record["fertility_quality_multiplier"], soil_derivation.fertility(self.world_map, tile_id), delta=ROUNDING, msg=tile_id)
            self.assertAlmostEqual(record["heavy_soil_share"], soil_derivation.heavy_soil_share(self.world_map, tile_id), delta=ROUNDING, msg=tile_id)

    def test_the_mediterranean_is_the_reference_field_and_the_desert_and_ice_are_not(self):
        self.assertAlmostEqual(self.median("Csa", soil_derivation.fertility), 1.0, delta=0.1)
        self.assertGreater(self.median("Csa", soil_derivation.arable_fraction), 0.3)
        self.assertLess(self.median("BWh", soil_derivation.arable_fraction), 0.05)
        self.assertEqual(self.median("EF", soil_derivation.arable_fraction), 0.0)

    def test_dryness_cuts_the_arable_share_and_a_short_season_cuts_it_too(self):
        self.assertGreater(self.median("BSh", soil_derivation.arable_fraction), self.median("BWh", soil_derivation.arable_fraction))
        self.assertGreater(self.median("Csa", soil_derivation.arable_fraction), self.median("BSh", soil_derivation.arable_fraction))
        self.assertGreater(self.median("Dfb", soil_derivation.arable_fraction), self.median("Dfc", soil_derivation.arable_fraction))
        self.assertGreater(self.median("Dfc", soil_derivation.arable_fraction), self.median("ET", soil_derivation.arable_fraction))

    def test_rain_far_beyond_evaporation_on_hot_ground_leaches_it(self):
        self.assertLess(self.median("Af", soil_derivation.fertility), self.median("Cfa", soil_derivation.fertility))

    def test_heavy_soil_collects_on_flat_wet_ground_not_on_rugged_or_dry_ground(self):
        flat_wet = [tile_id for tile_id in self.world_map.tiles
                    if (soil_derivation.aridity_index(self.world_map, tile_id) or 0.0) > 1.2
                    and tile_layers.number(self.world_map, tile_id, "ruggedness_index", 0.0) < 30.0]
        dry = self.tiles_of_class("BWh")
        self.assertTrue(flat_wet)
        for tile_id in flat_wet:
            self.assertGreater(soil_derivation.heavy_soil_share(self.world_map, tile_id), 0.0, tile_id)
        for tile_id in dry:
            self.assertEqual(soil_derivation.heavy_soil_share(self.world_map, tile_id), 0.0, tile_id)

    def test_every_value_is_a_share(self):
        for tile_id in self.world_map.tiles:
            for rule in (soil_derivation.arable_fraction, soil_derivation.heavy_soil_share):
                self.assertTrue(0.0 <= rule(self.world_map, tile_id) <= 1.0, tile_id)
            self.assertGreaterEqual(soil_derivation.fertility(self.world_map, tile_id), 0.0, tile_id)

    def test_derived_values_lie_near_the_old_table_by_class(self):
        arable_error = fertility_error = count = 0.0
        by_class = defaultdict(list)
        for tile_id, record in self.world_map.tiles.items():
            by_class[record["koppen_class"]].append(tile_id)
        for koppen_class, tile_ids in by_class.items():
            table_arable, table_fertility = KOPPEN_ARABLE_AND_FERTILITY[koppen_class]
            for tile_id in tile_ids:
                arable_error += abs(soil_derivation.arable_fraction(self.world_map, tile_id) - table_arable)
                fertility_error += abs(soil_derivation.fertility(self.world_map, tile_id) - table_fertility)
                count += 1
            if len(tile_ids) >= MINIMUM_TILES_PER_CLASS and table_arable > 0.05:
                self.assertAlmostEqual(self.median(koppen_class, soil_derivation.arable_fraction), table_arable,
                                       delta=CLASS_MEDIAN_ARABLE_TOLERANCE, msg=koppen_class)
                self.assertAlmostEqual(self.median(koppen_class, soil_derivation.fertility), table_fertility,
                                       delta=CLASS_MEDIAN_FERTILITY_TOLERANCE, msg=koppen_class)
        self.assertLess(arable_error / count, MEAN_ARABLE_ERROR_LIMIT)
        self.assertLess(fertility_error / count, MEAN_FERTILITY_ERROR_LIMIT)


if __name__ == "__main__":
    unittest.main()
