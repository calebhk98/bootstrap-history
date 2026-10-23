"""Complaint 543: a tile's soil nitrogen is a stock that harvests draw down and fallow, legumes and manure restore.

The pure stock (sim/geography/soil_nutrients.py) is tested on its own; the tile's yield factor reading it is tested
through geography's crop_site; the save round trip and the yearly step are tested in test_soil_nitrogen_held_land (no game) and
test_soil_nitrogen_whole_game."""

QUICK_TOPIC = True

import unittest

from sim.geography.api import crop_site, open_map, tiles_held
from sim.geography.api import soil_nutrients

WHEAT_KG_PER_HECTARE = 1000.0
TWO_FIELD_CROPPED_SHARE = 0.5


def _years(share, years, **regime):
    """The pool share after `years` of the same regime."""
    for _ in range(years):
        share = soil_nutrients.next_share(share, **regime)
    return share


def _response(share, cropped_share=TWO_FIELD_CROPPED_SHARE, manure=0.0):
    return soil_nutrients.yield_response(share, cropped_share, TWO_FIELD_CROPPED_SHARE, manure)


class SoilNitrogenStockTests(unittest.TestCase):
    CONTINUOUS = dict(cropped_share=1.0, harvest_kg_per_cropped_hectare=WHEAT_KG_PER_HECTARE)

    def test_native_soil_under_the_reference_rotation_is_the_reference_field(self):
        self.assertAlmostEqual(_response(1.0), 1.0)

    def test_untouched_native_soil_stays_native(self):
        self.assertAlmostEqual(soil_nutrients.next_share(1.0, cropped_share=0.0, harvest_kg_per_cropped_hectare=0.0), 1.0)

    def test_continuous_wheat_lowers_the_pool_and_the_yield_year_on_year(self):
        shares = [1.0]
        for _ in range(40):
            shares.append(soil_nutrients.next_share(shares[-1], **self.CONTINUOUS))
        self.assertTrue(all(later < earlier for earlier, later in zip(shares, shares[1:])))
        self.assertLess(_response(shares[-1], 1.0), _response(shares[10], 1.0))
        self.assertLess(_response(shares[-1], 1.0), _response(1.0, 1.0))

    def test_the_decline_slows_as_the_pool_runs_down(self):
        first = 1.0 - soil_nutrients.next_share(1.0, **self.CONTINUOUS)
        depleted = _years(1.0, 200, **self.CONTINUOUS)
        last = depleted - soil_nutrients.next_share(depleted, **self.CONTINUOUS)
        self.assertLess(last, first / 2.0)
        self.assertGreater(depleted, 0.0)

    def test_a_fallow_year_restores_part_of_what_cropping_took(self):
        worn = _years(1.0, 40, **self.CONTINUOUS)
        rested = soil_nutrients.next_share(worn, cropped_share=0.0, harvest_kg_per_cropped_hectare=0.0)
        self.assertGreater(rested, worn)
        self.assertLess(rested, 1.0)

    def test_fallow_leaves_nitrate_for_the_next_crop(self):
        worn = _years(1.0, 40, **self.CONTINUOUS)
        self.assertGreater(_response(worn, 0.5), _response(worn, 1.0))

    def test_manure_raises_the_pool_and_the_yield(self):
        worn = _years(1.0, 40, **self.CONTINUOUS)
        plain = soil_nutrients.next_share(worn, **self.CONTINUOUS)
        manured = soil_nutrients.next_share(worn, manure_nitrogen_kg_per_hectare=40.0, **self.CONTINUOUS)
        self.assertGreater(manured, plain)
        self.assertGreater(_response(worn, 1.0, manure=40.0), _response(worn, 1.0))

    def test_legumes_in_the_rotation_hold_the_pool_up(self):
        plain = _years(1.0, 60, **self.CONTINUOUS)
        with_legumes = _years(1.0, 60, legume_share=0.25, **self.CONTINUOUS)
        self.assertGreater(with_legumes, plain)

    def test_a_manured_rotation_holds_what_an_unmanured_one_loses(self):
        manured = _years(1.0, 100, manure_nitrogen_kg_per_hectare=40.0, **self.CONTINUOUS)
        unmanured = _years(1.0, 100, **self.CONTINUOUS)
        self.assertGreater(manured, unmanured + 0.2)


class TileYieldReadsTheStockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world_map = open_map()
        cls.tile = max((tile for tile in cls.world_map.tiles
                        if crop_site(tile, 0.5, cls.world_map).cropped_hectares > 0.0),
                       key=lambda tile: crop_site(tile, 0.5, cls.world_map).cropped_hectares)

    def test_the_tiles_yield_factor_is_scaled_by_the_nutrient_factor(self):
        native = crop_site(self.tile, 0.5, self.world_map)
        worn = crop_site(self.tile, 0.5, self.world_map, nutrient_factor=0.8)
        self.assertAlmostEqual(worn.yield_factor, native.yield_factor * 0.8)
        self.assertEqual(worn.cropped_hectares, native.cropped_hectares)


if __name__ == "__main__":
    unittest.main()
