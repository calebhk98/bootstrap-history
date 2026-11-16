"""The compiled steps of the entry plans, each against the plain function it replaced, on inputs written out; and the plan table."""
QUICK_TOPIC = True

import math
import random
import unittest
from types import SimpleNamespace

import numpy

from sim.economy import entry_margin, entry_plan_table, entry_sizing
from sim.economy.entry_margin_kernel import streak_after, streak_has_lasted
from sim.economy.entry_plan_steps import (NO_TILE, SITES, SIZING, SiteTables, SizingTables, candidate_tiles, runs_supported, sized_runs_at,
                                          site_newcomer)

GOODS = ("clay", "fuel", "pot", "tool")


def recipe_and_tables(hard_inputs, plant_goods, outputs):
    """A recipe as the plain rule reads it, and the same recipe as the arrays the kernel reads (good columns follow GOODS)."""
    plain = SimpleNamespace(outputs=outputs, hard_inputs=hard_inputs, plant_goods=plant_goods)
    sizing = SIZING.new_table(SizingTables, 1, 1, widths={"hard_inputs": len(GOODS)})
    for good, quantity in hard_inputs.items():
        sizing.hard_inputs[0, GOODS.index(good)] = quantity
    made = numpy.zeros((1, len(GOODS)))
    plant = numpy.zeros((1, len(GOODS)))
    for good, quantity in outputs.items():
        made[0, GOODS.index(good)] = quantity
    for good, quantity in plant_goods.items():
        plant[0, GOODS.index(good)] = quantity
    return plain, made, plant, sizing


def traded_grid(volumes):
    """One tile; `volumes` maps a good to the units it carried (a good left out has no market: NaN)."""
    return numpy.array([[volumes.get(good, numpy.nan)] for good in GOODS])


class RunsSupportedTests(unittest.TestCase):
    def test_a_good_with_no_market_or_no_use_limits_nothing(self):
        self.assertTrue(math.isinf(runs_supported(numpy.nan, 2.0, 5.0)))
        self.assertTrue(math.isinf(runs_supported(40.0, 0.0, 5.0)))

    def test_a_market_that_carried_something_feeds_a_share_of_it_and_one_that_carried_nothing_the_trial_size(self):
        self.assertEqual(runs_supported(40.0, 2.0, 5.0), entry_sizing.ENTRY_SHARE_OF_INPUT_VOLUME * 40.0 / 2.0)
        self.assertEqual(runs_supported(0.0, 2.0, 5.0), 5.0)


class SizedRunsTests(unittest.TestCase):
    def test_the_size_is_the_plain_sizes_on_random_markets(self):
        generator = random.Random(3)
        for _case in range(300):
            hard = {good: generator.uniform(0.0, 3.0) for good in ("clay", "fuel") if generator.random() < 0.7}
            plant = {"tool": generator.uniform(0.0, 2.0)} if generator.random() < 0.5 else {}
            plain, made, plant_matrix, sizing = recipe_and_tables(hard, plant, {"pot": generator.uniform(0.5, 4.0)})
            volumes = {good: generator.choice((0.0, generator.uniform(0.0, 80.0))) for good in GOODS if generator.random() < 0.8}
            grid = traded_grid(volumes)
            traded = lambda good, tile: volumes.get(good)           # noqa: E731
            gap, whole, unfilled = generator.uniform(0.0, 50.0), generator.uniform(1.0, 90.0), generator.choice((0.0, 7.0))
            expected = entry_sizing.sized_runs(plain, "pot", gap, whole, "T", traded, None, unfilled)
            found = sized_runs_at(0, GOODS.index("pot"), gap, whole, 0, NO_TILE, unfilled, grid, made, plant_matrix, sizing)
            self.assertEqual(found, expected)


class StreakTests(unittest.TestCase):
    def test_the_streak_and_its_having_lasted_are_the_plain_rules(self):
        for years in range(0, 8):
            for expected_price, entry_price in ((2.0, 1.0), (1.0, 1.0), (0.5, 1.0)):
                self.assertEqual(streak_after(years, expected_price, entry_price), entry_margin.margin_streak(years, expected_price, entry_price))
            self.assertEqual(streak_has_lasted(years), entry_margin.margin_has_lasted(years))


def site_arrays(tiles, runs_anywhere, sited=False, order=()):
    """One recipe's `SiteTables` over `tiles` tiles that fits everywhere."""
    sites = SITES.new_table(SiteTables, 1, 1, widths={"order": tiles, "fits": tiles, "suited": tiles, "supply_tiles": tiles})
    sites.sited[0], sites.runs_anywhere[0], sites.hours_per_run[0] = sited, runs_anywhere, 2.0
    sites.fits[0] = True
    sites.suited[0] = True
    sites.order_count[0] = len(order)
    sites.order[0, :len(order)] = order
    return sites


def no_fallbacks():
    """The tool-fallback tables (entry_wear_kernel) of one recipe with no tool wear."""
    none = numpy.full((1, 1), -1, dtype=numpy.int64)
    return (none, none, none, numpy.zeros((1, 1)), numpy.zeros((1, 1)), numpy.full((1, 1, 1), -1, dtype=numpy.int64), none, numpy.zeros((1, 1)))


class SitingTests(unittest.TestCase):
    def test_a_recipe_that_runs_anywhere_is_sited_on_the_anchor_and_books_its_runs_and_hours(self):
        capacity, committed = numpy.zeros((1, 3)), numpy.zeros(3)
        state = (numpy.zeros((1, 1)), numpy.zeros((1, 3)), numpy.zeros((1, 3), dtype=bool), numpy.zeros((3, 3)), numpy.full((1, 3), numpy.nan),
                 numpy.ones((1, 3)), numpy.full((1, 3), numpy.inf), numpy.zeros(3, dtype=bool), numpy.full(3, 1e9), capacity, committed)
        tables = (numpy.zeros((3, 1, 1)), numpy.zeros((2, 1, 1)), numpy.full((1, 1), -1, dtype=numpy.int64), numpy.full((1, 1), -1, dtype=numpy.int64),
                  numpy.zeros((2, 3, 1)), numpy.zeros((3, 1)), numpy.zeros((1, 2)), numpy.zeros((3, 2)), numpy.zeros((1, 1)), numpy.zeros(3),
                  no_fallbacks())
        tile, runs = site_newcomer(0, 0, 1, 4.0, tables, state, site_arrays(3, True), numpy.zeros((1, 3), dtype=numpy.int64), False)
        self.assertEqual((tile, runs), (1, 4.0))
        self.assertEqual((capacity[0, 1], committed[1]), (4.0, 8.0))

    def test_a_sited_recipe_tries_its_own_order_and_an_unsited_one_the_suited_tiles_of_the_market_area(self):
        sited = site_arrays(4, False, True, order=(3, 1))
        self.assertEqual(candidate_tiles(0, 0, 0, sited, numpy.zeros((1, 4), dtype=numpy.int64)).tolist(), [3, 1])
        unsited = site_arrays(4, False)
        unsited.suited[0, 2] = False
        area_of_tile = numpy.array([[0, 0, 0, 1]], dtype=numpy.int64)
        self.assertEqual(candidate_tiles(0, 0, 0, unsited, area_of_tile).tolist(), [0, 1])


class PlanTableTests(unittest.TestCase):
    def test_joined_tables_hold_the_first_plans_then_the_second(self):
        first = entry_plan_table.ENTRY_PLANS.table_of(entry_plan_table.EntryPlans, recipe_row=[1], tile_row=[2], good_col=[3], runs=[4.0],
                                                      yearly_return=[0.5])
        second = entry_plan_table.ENTRY_PLANS.table_of(entry_plan_table.EntryPlans, recipe_row=[5, 6], tile_row=[7, 8], good_col=[9, 1],
                                                       runs=[1.0, 2.0], yearly_return=[0.1, 0.2])
        both = entry_plan_table.joined(first, second)
        self.assertEqual(entry_plan_table.count(both), 3)
        self.assertEqual(both.recipe_row[:3].tolist(), [1, 5, 6])
        self.assertEqual(both.runs[:3].tolist(), [4.0, 1.0, 2.0])


if __name__ == "__main__":
    unittest.main()
