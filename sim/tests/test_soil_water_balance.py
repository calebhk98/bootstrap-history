"""Complaint 543: the water balance behind a tile's arable share and fertility. Each rule is called on numbers built in the
test; the anchor is FAO-56 (Allen et al. 1998) chapter 3 Example 8, opened at fao.org/4/x0490e/x0490e07.htm."""
QUICK_TOPIC = True

import unittest

from sim.geography import soil_water_balance as balance

DAILY_RANGE_C = 10.0


class ExtraterrestrialRadiationTests(unittest.TestCase):
    def test_matches_the_fao_worked_example(self):
        # FAO-56 Example 8: 3 September (day 246) at 20 degrees south, 32.2 MJ per m2 a day, 13.1 mm a day.
        self.assertAlmostEqual(balance.extraterrestrial_radiation_mm_per_day(-20.0, 246), 13.1, delta=0.1)

    def test_polar_winter_has_no_sun_and_summer_has_more_than_the_equator(self):
        self.assertAlmostEqual(balance.extraterrestrial_radiation_mm_per_day(85.0, 355), 0.0, delta=0.05)
        self.assertGreater(balance.extraterrestrial_radiation_mm_per_day(60.0, 172),
                           balance.extraterrestrial_radiation_mm_per_day(0.0, 172))


class EvaporationTests(unittest.TestCase):
    def test_a_hot_tile_evaporates_more_than_a_cool_one_at_the_same_latitude(self):
        hot = balance.evaporation_mm_per_year(35.0, 24.0, 14.0, 34.0, DAILY_RANGE_C)
        cool = balance.evaporation_mm_per_year(35.0, 12.0, 2.0, 22.0, DAILY_RANGE_C)
        self.assertGreater(hot, cool)

    def test_a_frozen_year_evaporates_nothing(self):
        self.assertEqual(balance.evaporation_mm_per_year(80.0, -20.0, -30.0, -2.0, DAILY_RANGE_C), 0.0)

    def test_a_larger_daily_range_raises_evaporation(self):
        narrow = balance.evaporation_mm_per_year(40.0, 14.0, 4.0, 24.0, 6.0)
        wide = balance.evaporation_mm_per_year(40.0, 14.0, 4.0, 24.0, 14.0)
        self.assertGreater(wide, narrow)

    def test_mediterranean_evaporation_is_of_the_order_of_a_metre_a_year(self):
        # Rome-like: 15 C mean, 7 C coldest month, 24 C warmest, 42 degrees north.
        evaporation = balance.evaporation_mm_per_year(42.0, 15.5, 7.0, 24.0, DAILY_RANGE_C)
        self.assertGreater(evaporation, 800.0)
        self.assertLess(evaporation, 1400.0)

    def test_southern_hemisphere_summer_is_the_warm_half_of_its_own_year(self):
        north = balance.evaporation_mm_per_year(40.0, 14.0, 4.0, 24.0, DAILY_RANGE_C)
        south = balance.evaporation_mm_per_year(-40.0, 14.0, 4.0, 24.0, DAILY_RANGE_C)
        self.assertAlmostEqual(north, south, delta=0.03 * north)


class AridityAndSeasonTests(unittest.TestCase):
    def test_aridity_index_is_rain_over_evaporation(self):
        self.assertAlmostEqual(balance.aridity_index(600.0, 1000.0), 0.6)

    def test_no_evaporation_gives_no_index_not_zero(self):
        self.assertIsNone(balance.aridity_index(600.0, 0.0))

    def test_months_above_a_threshold_follow_the_sine(self):
        self.assertAlmostEqual(balance.months_at_or_above(5.0, 15.0, 5.0, 25.0), 12.0, delta=0.2)
        self.assertAlmostEqual(balance.months_at_or_above(15.0, 15.0, 5.0, 25.0), 6.0, delta=0.2)
        self.assertEqual(balance.months_at_or_above(30.0, 15.0, 5.0, 25.0), 0.0)
