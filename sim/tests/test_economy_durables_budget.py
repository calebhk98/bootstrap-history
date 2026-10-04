"""A durable's stock is built from the year's spending, not from every unit of cash; at the stock that
serves the flow it is bought at its wear rate."""
import unittest

from sim.economy import households
from sim.economy.households_orders import _durable_ratio
from sim.economy.types import GoodSpec
from sim.tests.test_economy_households import BASKET, SPECS, View, cohort

PLOUGH_LIFE = SPECS["plough"].service_life_years


class DurableRatioTests(unittest.TestCase):
    def test_a_good_without_a_service_life_is_bought_in_full(self):
        self.assertEqual(_durable_ratio("grain", 10.0, 99.0, SPECS), 1.0)

    def test_nothing_held_wants_the_stock_for_the_whole_life(self):
        self.assertAlmostEqual(_durable_ratio("plough", 10.0, 0.0, SPECS), PLOUGH_LIFE)

    def test_at_the_serving_stock_only_the_wear_is_replaced(self):
        flow = 10.0
        self.assertAlmostEqual(_durable_ratio("plough", flow, flow * PLOUGH_LIFE, SPECS), 1.0)

    def test_beyond_the_serving_stock_nothing_is_bought(self):
        self.assertEqual(_durable_ratio("plough", 10.0, 1e6, SPECS), 0.0)

    def test_between_it_is_the_gap_plus_the_wear_over_the_flow(self):
        specs = {"plough": GoodSpec("plough", 10.0, 0.0, 4.0, "tool")}
        self.assertAlmostEqual(_durable_ratio("plough", 10.0, 20.0, specs), (40.0 - 20.0 + 5.0) / 10.0)


class DurableBudgetTests(unittest.TestCase):
    def test_stocking_up_costs_no_more_than_a_year_of_the_same_good_used_up(self):
        used_up = dict(SPECS, plough=GoodSpec("plough", 10.0, 0.0, 0.0, "tool"))
        durable_bids = households.goods_orders(cohort(), View(), 60000.0, 30000.0, BASKET, SPECS).bids
        used_up_bids = households.goods_orders(cohort(), View(), 60000.0, 30000.0, BASKET, used_up).bids
        self.assertLessEqual(sum(bid.budget for bid in durable_bids),
                             sum(bid.budget for bid in used_up_bids) * (1.0 + 1e-6))


if __name__ == "__main__":
    unittest.main()
