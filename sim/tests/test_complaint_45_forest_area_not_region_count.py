"""Complaints/45, the forest half: the woodland a civilisation can hold follows the ground it holds, not the number of
region labels the ground is filed under. The rule is sim/resources/ceilings.py, called on civilisations built here
and read against the real map (no game is built)."""
QUICK_TOPIC = True

import unittest

from sim.engine.data import load_civ
from sim.resources import constants as resource_constants
from sim.resources.ceilings import forest_ceiling_hectares, revenue_scale_multiple
from sim.geography.api import layer_value, open_map
from sim.tests import land_host

WORLD_MAP = open_map()


def held_land_area_km2(civilisation, world_map):
    """The land area the land module gives the tiles the civilisation holds on the map."""
    module = land_host.build(civilisation)
    module._map_cache = world_map
    return module.land_area_of(module.tiles_listed_by(civilisation))
REACH = 0.6
BASE = resource_constants.FOREST_HA_PER_MILLION_KM2_BASE
PER_CAPACITY = resource_constants.FOREST_HA_PER_MILLION_KM2_PER_SC


def territory(*region_labels):
    """A civilisation holding the tiles its region labels name (and no listed tiles)."""
    return {"id": "built_for_test", "home_regions": list(region_labels)}


def area_of_labelled_tiles(*region_labels):
    return sum(float(tile["land_area_km2"]) for tile_id, tile in WORLD_MAP.tiles.items()
               if layer_value(tile_id, "region", WORLD_MAP) in region_labels)


def ceiling_of(civilisation, state_reach=REACH, revenue_multiple=1.0):
    return forest_ceiling_hectares(held_land_area_km2(civilisation, WORLD_MAP), state_reach, BASE, PER_CAPACITY,
                                   revenue_multiple)


class HeldLandAreaTests(unittest.TestCase):
    def test_one_region_is_the_area_of_its_tiles_not_one_region(self):
        self.assertAlmostEqual(held_land_area_km2(territory("italia"), WORLD_MAP), area_of_labelled_tiles("italia"))

    def test_two_regions_are_the_sum_of_their_areas_not_a_count_of_two(self):
        self.assertAlmostEqual(held_land_area_km2(territory("italia", "britannia"), WORLD_MAP),
                               area_of_labelled_tiles("italia", "britannia"))

    def test_a_civilisation_that_resolves_to_no_tile_holds_no_land(self):
        self.assertEqual(held_land_area_km2(territory("not_a_real_region_id"), WORLD_MAP), 0.0)

    def test_listed_tiles_win_over_region_labels(self):
        listed = {"id": "built_for_test", "home_tiles": [sorted(WORLD_MAP.tiles)[0]], "home_regions": ["italia"]}
        self.assertAlmostEqual(held_land_area_km2(listed, WORLD_MAP),
                               float(WORLD_MAP.tiles[sorted(WORLD_MAP.tiles)[0]]["land_area_km2"]))


class CeilingFormulaTests(unittest.TestCase):
    def test_the_ceiling_is_proportional_to_land_area(self):
        one = forest_ceiling_hectares(1.0e6, REACH, BASE, PER_CAPACITY, 1.0)
        self.assertAlmostEqual(forest_ceiling_hectares(3.0e6, REACH, BASE, PER_CAPACITY, 1.0), 3.0 * one)

    def test_a_more_capable_state_holds_more_of_the_same_ground(self):
        self.assertGreater(forest_ceiling_hectares(1.0e6, 0.9, BASE, PER_CAPACITY, 1.0),
                           forest_ceiling_hectares(1.0e6, 0.1, BASE, PER_CAPACITY, 1.0))

    def test_a_million_square_kilometres_holds_base_plus_the_capacity_term(self):
        self.assertAlmostEqual(forest_ceiling_hectares(1.0e6, 0.5, 1000.0, 2000.0, 1.0), 2000.0)

    def test_no_land_no_woodland(self):
        self.assertEqual(forest_ceiling_hectares(0.0, 1.0, BASE, PER_CAPACITY, 5.0), 0.0)

    def test_the_revenue_multiple_scales_the_ceiling(self):
        plain = forest_ceiling_hectares(1.0e6, REACH, BASE, PER_CAPACITY, 1.0)
        self.assertAlmostEqual(forest_ceiling_hectares(1.0e6, REACH, BASE, PER_CAPACITY, 2.5), 2.5 * plain)


class RevenueMultipleTests(unittest.TestCase):
    def test_no_revenue_adds_nothing(self):
        self.assertEqual(revenue_scale_multiple(0.0, 100.0, 5.0), 1.0)

    def test_negative_revenue_adds_nothing(self):
        self.assertEqual(revenue_scale_multiple(-50.0, 100.0, 5.0), 1.0)

    def test_revenue_adds_its_share_of_the_scale(self):
        self.assertAlmostEqual(revenue_scale_multiple(250.0, 100.0, 5.0), 3.5)

    def test_the_revenue_part_is_capped(self):
        self.assertEqual(revenue_scale_multiple(1.0e9, 100.0, 5.0), 6.0)


class AreaNotRegionCountTests(unittest.TestCase):
    """Real geography: territories of near-equal area get near-equal ceilings whatever their label count."""

    def test_rome_and_a_single_region_china_stand_in_have_comparable_land(self):
        rome = held_land_area_km2(load_civ("rome_100ad"), WORLD_MAP)
        china = held_land_area_km2(territory("china"), WORLD_MAP)
        self.assertLess(abs(rome - china) / max(rome, china), 0.05, (rome, china))

    def test_with_state_capacity_held_equal_their_ceilings_agree(self):
        rome = ceiling_of(load_civ("rome_100ad"))
        china = ceiling_of(territory("china"))
        self.assertLess(abs(rome - china) / max(rome, china), 0.10, (rome, china))

    def test_one_region_and_two_regions_of_nearly_the_same_area_get_nearly_the_same_ceiling(self):
        one, two = territory("levant_mesopotamia"), territory("britannia", "italia")
        area_one, area_two = held_land_area_km2(one, WORLD_MAP), held_land_area_km2(two, WORLD_MAP)
        # the comparison means something only while the two territories are close in area
        self.assertLess(abs(area_one - area_two) / max(area_one, area_two), 0.05, (area_one, area_two))
        self.assertLess(abs(ceiling_of(one) - ceiling_of(two)) / max(ceiling_of(one), ceiling_of(two)), 0.05)

    def test_a_civilisation_that_resolves_to_no_tile_has_no_woodland_ceiling(self):
        self.assertEqual(ceiling_of(territory("not_a_real_region_id")), 0.0)


class RomeCalibrationTests(unittest.TestCase):
    """A validation: Rome is the one territory the area constants were calibrated against."""

    def test_rome_before_revenue_is_near_the_figure_the_old_region_count_formula_gave(self):
        old_formula_ceiling = 31325.0
        rome = load_civ("rome_100ad")
        ceiling = ceiling_of(rome, 0.85)   # the reach the old calibration took for Rome
        self.assertLess(abs(ceiling - old_formula_ceiling) / old_formula_ceiling, 0.10, ceiling)


if __name__ == "__main__":
    unittest.main()
