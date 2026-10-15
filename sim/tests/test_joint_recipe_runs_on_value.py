"""Complaint 473: a joint recipe is held back by unsold stock only when what a run can still sell does not cover
the run's cost; an unsold main output does not stop a run whose other output pays for it."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import producers
from sim.economy.types import Recipe

# a run makes a lot of slag nobody buys and a little gem that sells dear
JOINT = Recipe("joint", {"slag": 1000.0, "gem": 1.0}, {"ore": 10.0}, {"hand": 5.0})
PRICES = {"slag": 0.001, "gem": 100.0, "ore": 1.0}
WAGES = {"hand": 1.0}
FLOOR = 5.0 - producers.OUTPUT_CHANGE_SHARE_PER_YEAR * 10.0      # the fewest runs a year may fall to from 5
RUN_COST = 10.0 * 1.0 + 5.0 * 1.0


class View:
    year = 3

    def __init__(self, held, prices=PRICES):
        self.held, self.prices = held, prices

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return WAGES.get(trade)

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def cash(self, agent, currency):
        return 1e9

    def stock(self, agent, good, tile):
        return self.held.get(good, 0.0)


def producer(**changes):
    base = dict(agent_id="j1", owner="lord", recipe_id="joint", tile="t", capacity_runs=10.0, last_runs=5.0,
                expected_sales=5.0, expected_prices={"slag": 0.001, "gem": 100.0})
    base.update(changes)
    return producers.Producer(**base)


class JointRecipeStockTests(unittest.TestCase):
    def test_an_unsold_main_output_does_not_stop_runs_while_the_by_product_pays_for_them(self):
        view = View({"slag": 500.0 * 1000.0})
        self.assertEqual(producers.runs_for_stock(producer(), JOINT, view), 0.0)       # judged on stock alone it stops
        runs = producers.runs_for_stock(producer(), JOINT, view, RUN_COST, {"slag": 0.001, "gem": 100.0})
        self.assertTrue(math.isinf(runs))

    def test_runs_stop_when_what_still_sells_does_not_cover_the_run(self):
        view = View({"slag": 500.0 * 1000.0})
        runs = producers.runs_for_stock(producer(), JOINT, view, RUN_COST, {"slag": 0.001, "gem": 1.0})
        self.assertEqual(runs, 0.0)

    def test_the_plan_keeps_running_on_the_by_product(self):
        view = View({"slag": 500.0 * 1000.0})
        plan = producers.plan(producer(), JOINT, view, 1e9)
        self.assertGreater(plan.runs, FLOOR)

    def test_the_plan_stops_when_the_by_product_does_not_pay(self):
        view = View({"slag": 500.0 * 1000.0}, dict(PRICES, gem=1.0))
        plan = producers.plan(producer(expected_prices={"slag": 0.001, "gem": 1.0}), JOINT, view, 1e9)
        self.assertLessEqual(plan.runs, FLOOR)      # only the year's allowed fall from last year's runs is left

    def test_a_pile_of_the_by_product_holds_runs_back_when_the_main_output_cannot_pay(self):
        view = View({"gem": 500.0})
        runs = producers.runs_for_stock(producer(), JOINT, view, RUN_COST, {"slag": 0.001, "gem": 100.0})
        self.assertLess(runs, 5.0)

    def test_a_single_output_recipe_is_judged_on_its_own_stock_as_before(self):
        single = Recipe("single", {"slag": 1000.0}, {"ore": 10.0}, {"hand": 5.0})
        view = View({"slag": 500.0 * 1000.0})
        self.assertEqual(producers.runs_for_stock(producer(recipe_id="single"), single, view, RUN_COST, {"slag": 0.001}), 0.0)


if __name__ == "__main__":
    unittest.main()
