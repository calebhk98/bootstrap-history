"""Complaint 473, owner question 6: a producer's plan chooses the share of workplaces that work on the level pair of its learning path
(`plan_level.level_share_working`), and the kernel (`plan_year.plans_of`) plans as `producers.plan` plans. Each test calls one function
with its inputs written out, except the kernel one, which compares the two plans of a small random economy (no game)."""

QUICK_TOPIC = True

import math
import unittest
from dataclasses import replace

from sim.economy import plan_level, plan_year, producers
from sim.economy.types import Recipe
from sim.economy.year_arrays import YearArrays
from sim.economy.year_arrays_costs import refreshed
from sim.tests.year_close_fixture import MONEY, economy_of

WORK = Recipe("work", {"grain": 1.0}, {"seed": 2.0}, {"hand": 10.0})
INPUTS = {"seed": 10.0}
WAGES = {"hand": 4.0}                  # a practised run costs 20 + 40


def share_on_level(output_price, crew_runs):
    return plan_level.level_share_working(WORK, crew_runs, 10.0, 1, 0.05, 1.0, {"grain": output_price}, INPUTS, WAGES, 0.0,
                                          producers.share_working)


class ShareWorkingOnTheLevelPair(unittest.TestCase):
    def test_a_recipe_that_pays_practised_gets_over_half_on_the_level_cost_where_the_first_year_gets_nearly_none(self):
        self.assertGreater(share_on_level(100.0, {"hand": 1.0}), 0.5)
        first_year_hours = 10.0 * 5.0                                         # a first attempt takes five times the booked hours
        first_year_share = producers.share_working(100.0 * 0.84, 20.0 + 4.0 * first_year_hours)
        self.assertLess(first_year_share, 0.01)

    def test_a_recipe_whose_practised_cost_is_above_its_revenue_gets_a_small_share(self):
        self.assertLess(share_on_level(55.0, {"hand": 1.0}), 0.1)

    def test_the_share_never_rises_as_revenue_falls(self):
        prices = [150.0, 120.0, 100.0, 80.0, 60.0, 40.0, 20.0, 5.0]
        shares = [share_on_level(price, {"hand": 1.0}) for price in prices]
        for higher, lower in zip(shares, shares[1:]):
            self.assertGreaterEqual(higher, lower)

    def test_a_crew_with_a_hundred_runs_a_year_is_judged_nearly_on_the_booked_cost(self):
        practised = producers.share_working(100.0, 60.0)
        self.assertLess(abs(share_on_level(100.0, {"hand": 100.0}) - practised), 0.1)


def with_crews(setup, record):
    """Every third producer an unpractised crew."""
    crewed = 0
    for producer_id in sorted(record.producers)[::3]:
        producer = record.producers[producer_id]
        crew = {trade: 1.0 for trade in sorted(setup.recipes[producer.recipe_id].labour_hours)}
        record.producers[producer_id] = replace(producer, crew_runs=crew)
        crewed += 1
    return crewed


class KernelAndReferencePlanAgree(unittest.TestCase):
    def test_unpractised_crews_get_the_runs_the_plain_plan_gives_and_some_run(self):
        crewed_running = 0
        for seed in range(6):
            setup, record, view, _ledger, area_map = economy_of(seed, producer_count=60)
            crewed = with_crews(setup, record)
            self.assertGreater(crewed, 5)
            arrays = refreshed(YearArrays.build(setup, record, area_map, view), setup, record, view)
            plans = plan_year.plans_of(setup, record, view, arrays, MONEY)
            for producer_id in sorted(record.producers)[::3]:
                producer = record.producers[producer_id]
                plain = producers.plan(producer, setup.recipes[producer.recipe_id], view, record.book.balance(producer_id, MONEY))
                found = plans.plan_of(producer_id)
                self.assertTrue(math.isclose(found.runs, plain.runs, rel_tol=1e-8, abs_tol=1e-12), (producer_id, found.runs, plain.runs))
                crewed_running += plain.runs > 0.0
        self.assertGreater(crewed_running, 5)


if __name__ == "__main__":
    unittest.main()
