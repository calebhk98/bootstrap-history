"""Complaint 473: a durable a household keeps in use is not wealth it spends from. Counted as wealth, the stock
the opening seeds raised a cohort's spending, which made a dearer substitute affordable, and the substitute was
then bid for as a whole stock the opening sized its makers to build in year 0."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import households_orders, households_store

SERVICE_LIFE_YEARS = 50.0
FLOW = 1.0
PRICE = 10.0
SPECS = {"stone": types.SimpleNamespace(service_life_years=SERVICE_LIFE_YEARS),
         "silver": types.SimpleNamespace(service_life_years=0.0)}


def wealth_in_stores(held):
    """The store wealth the cohort spends from, with its needs keeping FLOW of stone a year in use."""
    prices = {"stone": PRICE, "silver": PRICE}
    with mock.patch.object(households_orders, "_smoothed_flow_by_good", lambda *_arguments: {"stone": FLOW}), \
            mock.patch.object(households_orders, "with_quality_reach", lambda priced, *_arguments: priced), \
            mock.patch.object(households_orders, "quality_reach", lambda *_arguments: 0.0):
        return households_orders._store_value_outside_use(
            types.SimpleNamespace(), [], None, SPECS, prices, prices, held, 100.0, 100.0, 0.0, 100.0, 50.0)


class DurablesInUseAreNotWealthTests(unittest.TestCase):
    def test_a_stock_no_larger_than_the_one_kept_in_use_is_not_wealth(self):
        self.assertEqual(wealth_in_stores({"stone": FLOW * SERVICE_LIFE_YEARS, "silver": 0.0}), 0.0)

    def test_only_the_stock_beyond_what_is_kept_in_use_is_wealth(self):
        in_use = FLOW * SERVICE_LIFE_YEARS * (1.0 + households_store.STORE_REBALANCE_BAND)
        held = {"stone": in_use + 7.0, "silver": 0.0}
        self.assertAlmostEqual(wealth_in_stores(held), 7.0 * PRICE, places=6)

    def test_a_store_good_without_a_service_life_is_all_wealth(self):
        self.assertEqual(wealth_in_stores({"stone": 0.0, "silver": 3.0}), 3.0 * PRICE)


if __name__ == "__main__":
    unittest.main()
