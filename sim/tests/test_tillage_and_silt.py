"""Complaint 543: heavy ground opens only to a toolkit that can pull it, and a flooding river's silt is the nitrogen input
of the land it waters (it replaces the old Nile rotation's yield multiplier). Rules are called on built tiles and numbers."""
QUICK_TOPIC = True

import unittest

from sim.geography import soil_nitrogen, soil_nutrients, tile_layers
from sim.geography.api import crop_site, open_map
from sim.world import agriculture, agriculture_tile, farming_technique

SHARE = 0.5
YEARS = 60
KG_PER_HECTARE = 1000.0


class TillageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world_map = open_map()
        cls.heavy_tile = max(cls.world_map.tiles, key=lambda tile_id: tile_layers.number(cls.world_map, tile_id, "heavy_soil_share", 0.0)
                             * tile_layers.number(cls.world_map, tile_id, "arable_fraction", 0.0))

    def test_the_chosen_tile_has_heavy_arable_ground(self):
        self.assertGreater(tile_layers.number(self.world_map, self.heavy_tile, "heavy_soil_share", 0.0), 0.2)

    def test_a_toolkit_that_cannot_pull_heavy_ground_opens_less_of_it(self):
        full = crop_site(self.heavy_tile, SHARE, self.world_map, tillage_capacity=1.0)
        ard = crop_site(self.heavy_tile, SHARE, self.world_map, tillage_capacity=agriculture.ARD_TILLAGE_CAPACITY)
        none = crop_site(self.heavy_tile, SHARE, self.world_map, tillage_capacity=0.0)
        heavy = tile_layers.number(self.world_map, self.heavy_tile, "heavy_soil_share", 0.0)
        self.assertGreater(full.arable_hectares, ard.arable_hectares)
        self.assertGreater(ard.arable_hectares, none.arable_hectares)
        self.assertAlmostEqual(none.arable_hectares, full.arable_hectares * (1.0 - heavy), delta=1e-6 * full.arable_hectares)
        self.assertGreater(full.cropped_hectares, ard.cropped_hectares)

    def test_a_tile_with_no_heavy_ground_does_not_care_about_the_toolkit(self):
        light = next(tile_id for tile_id in sorted(self.world_map.tiles)
                     if tile_layers.number(self.world_map, tile_id, "heavy_soil_share", 0.0) == 0.0
                     and tile_layers.number(self.world_map, tile_id, "arable_fraction", 0.0) > 0.1)
        self.assertEqual(crop_site(light, SHARE, self.world_map, tillage_capacity=0.0),
                         crop_site(light, SHARE, self.world_map, tillage_capacity=1.0))

    def test_the_heavy_plough_opens_what_the_ard_and_hoe_cannot(self):
        self.assertGreater(agriculture.HORSE_COLLAR_AND_MOULDBOARD.tillage_capacity, agriculture.DEFAULT_TOOLKIT.tillage_capacity)
        self.assertGreaterEqual(agriculture.DEFAULT_TOOLKIT.tillage_capacity, agriculture.HAND_HOE.tillage_capacity)

    def test_the_farm_models_crop_technique_carries_the_toolkits_capacity(self):
        for toolkit in (agriculture.HAND_HOE, agriculture.DEFAULT_TOOLKIT, agriculture.HORSE_COLLAR_AND_MOULDBOARD):
            technique = farming_technique.DEFAULT_TECHNIQUE._replace(toolkit=toolkit)
            self.assertEqual(agriculture_tile.crop_technique(technique).tillage_capacity, toolkit.tillage_capacity)

    def test_the_hoe_takes_more_hours_a_hectare_than_the_ard_and_no_more_yield(self):
        self.assertGreater(agriculture.HAND_HOE.labour_hours_multiplier, agriculture.DEFAULT_TOOLKIT.labour_hours_multiplier)
        self.assertEqual(agriculture.HAND_HOE.ploughing_yield_multiplier, agriculture.DEFAULT_TOOLKIT.ploughing_yield_multiplier)


class SiltTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world_map = open_map()

    def test_silt_nitrogen_is_depth_times_density_times_nitrogen_share(self):
        expected = (soil_nutrients.SILT_DEPOSITION_METRES_PER_YEAR * 10000.0 * soil_nutrients.SILT_BULK_DENSITY_KG_PER_CUBIC_METRE
                    * soil_nutrients.SILT_NITROGEN_FRACTION)
        self.assertAlmostEqual(soil_nutrients.SILT_NITROGEN_KG_PER_FLOODED_HECTARE, expected)
        self.assertGreater(expected, 0.0)

    def test_flooded_land_holds_a_higher_pool_under_continuous_cropping(self):
        def pool_after(flooded_share):
            pool = 1.0
            for _year in range(YEARS):
                pool = soil_nutrients.next_share(pool, 1.0, KG_PER_HECTARE, flooded_share=flooded_share)
            return pool
        self.assertGreater(pool_after(1.0), pool_after(0.0))
        self.assertGreater(pool_after(1.0), pool_after(0.5))

    def test_silt_adds_exactly_its_nitrogen_to_a_year_with_no_harvest(self):
        base = soil_nutrients.next_share(1.0, 1.0, 0.0)
        silted = soil_nutrients.next_share(1.0, 1.0, 0.0, flooded_share=1.0)
        self.assertAlmostEqual((silted - base) * soil_nutrients.NATIVE_POOL_KG_PER_HECTARE,
                               soil_nutrients.SILT_NITROGEN_KG_PER_FLOODED_HECTARE, places=6)

    def test_a_river_tile_has_flooded_hectares_and_a_dry_interior_tile_has_none(self):
        valley = max(self.world_map.tiles, key=lambda tile_id: crop_site(tile_id, SHARE, self.world_map).flooded_hectares)
        self.assertGreater(crop_site(valley, SHARE, self.world_map).flooded_hectares, 0.0)
        dry = next(tile_id for tile_id in sorted(self.world_map.tiles)
                   if tile_layers.number(self.world_map, tile_id, "river_km_all", 0.0) == 0.0)
        self.assertEqual(crop_site(dry, SHARE, self.world_map).flooded_hectares, 0.0)

    def test_the_stock_of_a_flooded_tile_is_kept_up_by_its_silt_in_the_yearly_step(self):
        valley = max(self.world_map.tiles, key=lambda tile_id: crop_site(tile_id, SHARE, self.world_map).flooded_hectares)
        site = crop_site(valley, SHARE, self.world_map)
        dry_site = site._replace(flooded_hectares=0.0)
        silted, unsilted = {}, {}
        for _year in range(YEARS):
            soil_nitrogen.step_year(silted, {valley: site}, KG_PER_HECTARE, 0.0, 0.5, 0.0)
            soil_nitrogen.step_year(unsilted, {valley: dry_site}, KG_PER_HECTARE, 0.0, 0.5, 0.0)
        self.assertGreater(silted[valley], unsilted[valley])

    def test_no_rotation_carries_a_yield_multiplier_of_its_own(self):
        self.assertNotIn("soil_fertility_yield_multiplier", agriculture.Rotation._fields)
        self.assertFalse(hasattr(agriculture, "NILE_FLOOD_RECESSION"))


if __name__ == "__main__":
    unittest.main()
