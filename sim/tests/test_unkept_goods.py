"""unkept_goods: which recipes make nothing that keeps a year, the sales their plan holds to, and the expected sales
their takings give."""

QUICK_TOPIC = True

import math
import unittest
from types import SimpleNamespace

import numpy as np

from sim.economy.unkept_goods import (cannot_be_kept, expected_sales_as_closed, expected_sales_by_takings_where_unkept,
                                      expected_takings_per_run, outputs_by_slot, recipes_that_cannot_be_kept, rows_that_cannot_be_kept,
                                      runs_its_takings_would_have_sold, stock_alone_where_kept)

SPECS = {"bread_kg": SimpleNamespace(spoilage_per_year=73.0), "milk_kg": SimpleNamespace(spoilage_per_year=1.0),
         "flour_kg": SimpleNamespace(spoilage_per_year=0.2), "bran_kg": SimpleNamespace(spoilage_per_year=0.1)}
RECIPES = {"bake": SimpleNamespace(outputs={"bread_kg": 1000.0}), "mill": SimpleNamespace(outputs={"flour_kg": 1000.0, "bran_kg": 150.0}),
           "dairy": SimpleNamespace(outputs={"milk_kg": 500.0, "bran_kg": 1.0}), "idle": SimpleNamespace(outputs={}),
           "strange": SimpleNamespace(outputs={"unknown_good": 1.0})}


class CannotBeKept(unittest.TestCase):
    def test_a_recipe_whose_every_output_spoils_within_the_year_cannot(self):
        self.assertTrue(cannot_be_kept(RECIPES["bake"], SPECS))

    def test_a_recipe_with_an_output_that_keeps_can(self):
        self.assertFalse(cannot_be_kept(RECIPES["mill"], SPECS))
        self.assertFalse(cannot_be_kept(RECIPES["dairy"], SPECS))

    def test_no_outputs_or_an_output_with_no_spec_counts_as_kept(self):
        self.assertFalse(cannot_be_kept(RECIPES["idle"], SPECS))
        self.assertFalse(cannot_be_kept(RECIPES["strange"], SPECS))

    def test_the_recipes_of_a_setup(self):
        self.assertEqual(recipes_that_cannot_be_kept(RECIPES, SPECS), frozenset({"bake"}))


class TheSalesAPlanHoldsTo(unittest.TestCase):
    def test_a_maker_of_goods_that_keep_is_held_by_its_stock_alone_and_one_of_goods_that_do_not_by_its_expected_sales(self):
        held = stock_alone_where_kept(np.array([40.0, 25.0, 0.0]), np.array([False, True, True]))
        self.assertTrue(math.isnan(held[0]))
        self.assertEqual(held[1:].tolist(), [25.0, 0.0])

    def test_the_figures_given_are_not_changed(self):
        expected = np.array([40.0, 25.0])
        stock_alone_where_kept(expected, np.array([False, True]))
        self.assertEqual(expected.tolist(), [40.0, 25.0])


class RunsItsTakingsWouldHaveSold(unittest.TestCase):
    def test_its_takings_over_what_a_run_was_expected_to_bring_in(self):
        self.assertAlmostEqual(runs_its_takings_would_have_sold(1200.0, 10.0), 120.0)

    def test_nothing_where_a_run_was_expected_to_bring_in_nothing(self):
        self.assertIsNone(runs_its_takings_would_have_sold(1200.0, 0.0))
        self.assertIsNone(runs_its_takings_would_have_sold(1200.0, math.nan))


class ExpectedSalesAfterTheClose(unittest.TestCase):
    CLOSED = np.array([50.0, 60.0, 70.0, 80.0])
    OLD = np.array([40.0, 100.0, 0.0, 30.0])
    TAKINGS = np.array([999.0, 1200.0, 900.0, 500.0])
    PER_RUN = np.array([10.0, 10.0, 10.0, 0.0])
    UNKEPT = np.array([False, True, True, True])

    def test_under_the_search_rules_the_close_stands(self):
        after = expected_sales_as_closed(self.CLOSED, self.OLD, self.TAKINGS, self.PER_RUN, self.UNKEPT, 0.2)
        self.assertEqual(after.tolist(), self.CLOSED.tolist())

    def test_a_maker_of_unkept_goods_moves_the_share_toward_the_runs_its_takings_would_have_sold(self):
        after = expected_sales_by_takings_where_unkept(self.CLOSED, self.OLD, self.TAKINGS, self.PER_RUN, self.UNKEPT, 0.2)
        self.assertAlmostEqual(after[1], 100.0 + 0.2 * (120.0 - 100.0))

    def test_one_that_expected_no_sales_takes_the_figure_whole(self):
        after = expected_sales_by_takings_where_unkept(self.CLOSED, self.OLD, self.TAKINGS, self.PER_RUN, self.UNKEPT, 0.2)
        self.assertAlmostEqual(after[2], 90.0)

    def test_makers_of_kept_goods_and_runs_expected_to_bring_in_nothing_keep_the_closes_figure(self):
        after = expected_sales_by_takings_where_unkept(self.CLOSED, self.OLD, self.TAKINGS, self.PER_RUN, self.UNKEPT, 0.2)
        self.assertEqual(after[0], 50.0)
        self.assertEqual(after[3], 80.0)

    def test_dear_sales_raise_expected_sales_and_cheap_ones_lower_them(self):
        old, per_run, unkept = np.array([100.0]), np.array([10.0]), np.array([True])
        dear = expected_sales_by_takings_where_unkept(np.array([100.0]), old, np.array([1300.0]), per_run, unkept, 0.2)[0]
        cheap = expected_sales_by_takings_where_unkept(np.array([100.0]), old, np.array([700.0]), per_run, unkept, 0.2)[0]
        self.assertGreater(dear, 100.0)
        self.assertLess(cheap, 100.0)


class RowsAndTakings(unittest.TestCase):
    def test_each_producer_row_reads_its_recipes_flag(self):
        mask = rows_that_cannot_be_kept(["bake", "mill"], np.array([1, 0, 0, 1]), RECIPES, SPECS)
        self.assertEqual(mask.tolist(), [False, True, True, False])

    def test_no_recipes_flags_nobody(self):
        self.assertEqual(rows_that_cannot_be_kept([], np.zeros(0, dtype=np.int64), RECIPES, SPECS).tolist(), [])

    def test_the_outputs_of_each_producers_recipe_laid_out_by_slot(self):
        outputs = np.array([[0.0, 1000.0, 150.0], [5.0, 0.0, 0.0]])       # recipes by goods
        slot_goods = np.array([[0, 1, 2], [0, -1, -1]])                   # recipes by slots; the first recipe's first slot is an input
        slot_is_output = np.array([[False, True, True], [True, False, False]])
        made = outputs_by_slot(outputs, slot_goods, slot_is_output, np.array([1, 0, 0]))
        self.assertEqual(made.tolist(), [[5.0, 0.0, 0.0], [0.0, 1000.0, 150.0], [0.0, 1000.0, 150.0]])

    def test_what_a_run_was_expected_to_bring_in_is_its_outputs_at_expected_prices_times_its_yield(self):
        outputs = np.array([[0.0, 1000.0, 150.0], [0.0, 1000.0, 0.0]])       # the first slot is an input
        prices = np.array([[0.4, 0.8, 0.1], [np.nan, 1.0, np.nan]])
        per_run = expected_takings_per_run(outputs, prices, np.array([1.0, 0.5]))
        self.assertAlmostEqual(per_run[0], 1000.0 * 0.8 + 150.0 * 0.1)
        self.assertAlmostEqual(per_run[1], 0.5 * 1000.0)


if __name__ == "__main__":
    unittest.main()
