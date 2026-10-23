"""A year of cash shortage, with the spending a household expects unchanged, does not make it offer the
durable stock that serves its needs: it offers at most the part of its holding above that stock."""

QUICK_TOPIC = True

import unittest

from sim.economy import durable_stock, households, households_orders, households_store
from sim.tests import economy_fixture as fixture
from sim.tests.economy_store_view import BASKET, SPECS, TILE, View, cohort, metal_held

EXPECTED_SPENDING = 200000.0
EXPECTED_FLOOR_COST = 7500.0
USUAL = (400000.0, EXPECTED_SPENDING)           # cash, income of an ordinary year
SHOCKS = ((40000.0, 20000.0), (8000.0, 2000.0), (4000.0, 0.0))     # cash, income after 90% to 99% is lost


def expecting_cohort():
    return cohort(expected_spending=EXPECTED_SPENDING, expected_floor_cost=EXPECTED_FLOOR_COST)


def in_use_kilograms():
    """The metal the expected flow keeps in use, with the store's rebalance band, as the household reads it."""
    priced = households_orders.need_prices(BASKET, View(), TILE)
    flow = households_orders._smoothed_flow_by_good(expecting_cohort(), priced, BASKET)
    return durable_stock.in_use_stock(flow, SPECS, 1.0, households_store.STORE_REBALANCE_BAND)[fixture.METAL]


def metal_offered(held, cash, income):
    result = households_orders.goods_orders(expecting_cohort(), View(stocks=metal_held(held)), cash, income,
                                            BASKET, SPECS)
    return sum(offer.quantity for offer in result.offers if offer.good == fixture.METAL)


class CashShockLeavesTheStockInUseTests(unittest.TestCase):
    def test_the_expected_flow_keeps_a_stock_in_use(self):
        self.assertGreater(in_use_kilograms(), 0.0)

    def test_a_stock_at_the_in_use_level_is_not_offered_in_any_year(self):
        in_use = in_use_kilograms()
        for cash, income in (USUAL,) + SHOCKS:
            self.assertEqual(metal_offered(in_use, cash, income), 0.0)

    def test_a_stock_below_the_in_use_level_is_not_offered_in_any_year(self):
        in_use = in_use_kilograms()
        for cash, income in (USUAL,) + SHOCKS:
            self.assertEqual(metal_offered(0.5 * in_use, cash, income), 0.0)

    def test_a_shock_year_offers_no_more_than_the_part_above_the_in_use_stock(self):
        in_use = in_use_kilograms()
        for multiple in (1.5, 3.0):
            held = multiple * in_use
            for cash, income in SHOCKS:
                self.assertLessEqual(metal_offered(held, cash, income), held - in_use)

    def test_a_shock_year_offers_close_to_what_an_ordinary_year_offers(self):
        held = 3.0 * in_use_kilograms()
        usual = metal_offered(held, *USUAL)
        self.assertGreater(usual, 0.0)
        for cash, income in SHOCKS:
            self.assertLess(metal_offered(held, cash, income), 1.05 * usual)


if __name__ == "__main__":
    unittest.main()
