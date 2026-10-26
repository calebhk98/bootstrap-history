"""Clearing land moves the rent the solver prices: the prices module's `price_tables` hands the solver the banded area
the farm has cleared, so a farm cleared into another band is re-priced and one moved within a band is not.
`prices.band_farmed_hectares` is the banding. The solver is a recorder; the stand-in game holds only what the method reads."""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.prices import prices

from sim.engine import data
from sim.tests import prices_stand_in

GRANTED = frozenset({"fire"})


def module_with(hectares):
    module = prices_stand_in.build(civilisation={"id": "test_civ", "starting_interest_rate": 0.1}, techniques_granted=GRANTED,
                                   techniques_in_use=GRANTED, farm_land_hectares=hectares)
    module.banded_market_rate = lambda: 0.1
    return module


def farmed_hectares_given_to_the_solver(hectares):
    asked = []

    def solver(granted, **keywords):
        asked.append(keywords["farmed_hectares"])
        return {"hectare_land": 1.0}, {"hectare_land": "derived"}

    with mock.patch.object(data, "calculated_goods_table", solver):
        module_with(hectares).price_tables()
    return asked


class PriceTablesTests(unittest.TestCase):
    def test_the_solver_is_given_a_band_around_the_cleared_area(self):
        (given,) = farmed_hectares_given_to_the_solver(1000.0)
        self.assertLessEqual(max(given / 1000.0, 1000.0 / given), prices.FARMED_AREA_BAND_RATIO)

    def test_a_farm_cleared_into_another_band_is_priced_at_another_area(self):
        small = farmed_hectares_given_to_the_solver(1000.0)
        large = farmed_hectares_given_to_the_solver(3000.0)
        self.assertNotEqual(small, large)

    def test_a_farm_moved_within_a_band_is_priced_at_the_same_area(self):
        self.assertEqual(farmed_hectares_given_to_the_solver(1000.0), farmed_hectares_given_to_the_solver(1001.0))


class BandTests(unittest.TestCase):
    def test_no_cleared_area_has_no_band(self):
        self.assertIsNone(prices.band_farmed_hectares(0.0))
        self.assertIsNone(prices.band_farmed_hectares(None))

    def test_a_band_is_a_geometric_step_and_a_larger_area_never_gets_a_lower_band(self):
        areas = [100.0, 300.0, 1000.0, 3000.0, 10000.0]
        bands = [prices.band_farmed_hectares(area) for area in areas]
        self.assertEqual(bands, sorted(bands))
        self.assertEqual(len(set(bands)), len(bands))


if __name__ == "__main__":
    unittest.main()
