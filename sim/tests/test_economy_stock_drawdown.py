"""Complaint 473: a producer holding excess stock works it off over STOCK_CLEARING_YEARS and keeps working while the
stock will clear in them, instead of planning no runs the year its stock passes its expected sales. Rule tests on a
built producer and a view."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import inventory, producers
from sim.economy.types import Recipe

FARM = Recipe("farm", {"grain": 10.0}, {}, {"hand": 5.0})
EXPECTED_SALES = 5.0        # runs a year
TARGET_RUNS = inventory.target_stock(EXPECTED_SALES)


class View:
    year = 3

    def __init__(self, stock_runs):
        self.held = stock_runs * FARM.outputs["grain"]

    def price(self, good, area):
        return 2.0 if good == "grain" else None

    def wage(self, trade, area):
        return 1.0

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def cash(self, agent, currency):
        return 1e6

    def stock(self, agent, good, tile):
        return self.held if good == "grain" else 0.0


def farmer(**changes):
    base = dict(agent_id="f1", owner="lord", recipe_id="farm", tile="t", capacity_runs=10.0, last_runs=5.0,
                expected_sales=EXPECTED_SALES, expected_prices={"grain": 2.0})
    base.update(changes)
    return producers.Producer(**base)


class StockDrawdownTests(unittest.TestCase):
    def test_stock_below_target_plans_expected_sales_plus_the_shortfall_over_the_clearing_years(self):
        runs = producers.runs_for_stock(farmer(), FARM, View(0.5 * TARGET_RUNS))
        self.assertAlmostEqual(runs, EXPECTED_SALES + 0.5 * TARGET_RUNS / producers.STOCK_CLEARING_YEARS)

    def test_stock_at_target_plans_expected_sales(self):
        self.assertAlmostEqual(producers.runs_for_stock(farmer(), FARM, View(TARGET_RUNS)), EXPECTED_SALES)

    def test_no_record_of_sales_does_not_limit_runs(self):
        self.assertTrue(math.isinf(producers.runs_for_stock(farmer(expected_sales=0.0), FARM, View(0.0))))

    def test_excess_is_drawn_down_over_the_clearing_years(self):
        excess = 2.0
        runs = producers.runs_for_stock(farmer(), FARM, View(TARGET_RUNS + excess))
        self.assertAlmostEqual(runs, EXPECTED_SALES - excess / producers.STOCK_CLEARING_YEARS)

    def test_stock_that_clears_within_the_years_never_plans_zero_runs(self):
        for share in (0.2, 0.5, 0.9, 0.99):
            excess = share * producers.STOCK_CLEARING_YEARS * EXPECTED_SALES
            runs = producers.runs_for_stock(farmer(), FARM, View(TARGET_RUNS + excess))
            self.assertGreater(runs, 0.0, share)

    def test_stock_that_cannot_clear_within_the_years_plans_none(self):
        excess = 1.01 * producers.STOCK_CLEARING_YEARS * EXPECTED_SALES
        self.assertEqual(producers.runs_for_stock(farmer(), FARM, View(TARGET_RUNS + excess)), 0.0)

    def test_planned_runs_fall_as_stock_rises_and_more_stock_never_plans_more(self):
        runs = [producers.runs_for_stock(farmer(), FARM, View(TARGET_RUNS + excess)) for excess in (0.1, 1.0, 3.0, 6.0, 20.0)]
        self.assertEqual(runs, sorted(runs, reverse=True))

    def test_a_producer_with_a_positive_margin_and_clearing_stock_plans_runs_in_its_year(self):
        # stock four runs over target against five sold a year: the old gate (sales less the whole excess) planned one run
        who = farmer(last_runs=5.0)
        plan = producers.plan(who, FARM, View(TARGET_RUNS + 4.0), 1e6)
        self.assertGreater(plan.expected_margin_per_run, 0.0)
        self.assertAlmostEqual(plan.runs, EXPECTED_SALES - 4.0 / producers.STOCK_CLEARING_YEARS)
        self.assertGreater(plan.runs, EXPECTED_SALES - 4.0)


if __name__ == "__main__":
    unittest.main()
