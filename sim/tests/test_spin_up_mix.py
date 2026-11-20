"""spin_up_mix and spin_up_mix_table: what a spin-up year's economy is made of, and the first year, the trough and the
last year side by side."""

QUICK_TOPIC = True

import unittest

from sim.economy.market_memory import market_key
from sim.economy.spin_up_mix import hours_by_trade, made_by_recipe, runs_by_recipe, stock_by_good, value_by_good
from sim.markets.spin_up_ensemble import median_by_good
from sim.markets.spin_up_mix_table import largest_first, marked_rows, recipe_shares, recipes_that_moved, trough


class HoursByTrade(unittest.TestCase):
    def test_hired_and_idle_hours_are_summed_over_a_trades_areas(self):
        keys = [market_key("farmer", "north"), market_key("farmer", "south"), market_key("mason", "north")]
        self.assertEqual(hours_by_trade(keys, [10.0, 20.0, 5.0], [1.0, 2.0, 0.0]), {"farmer": (30.0, 3.0), "mason": (5.0, 0.0)})


class RunsByRecipe(unittest.TestCase):
    def test_runs_and_capacity_are_summed_by_recipe_and_a_producer_that_has_not_run_counts_none(self):
        producers = [("mill", 4.0, 10.0), ("mill", -1.0, 5.0), ("bakery", 2.0, 2.0)]
        self.assertEqual(runs_by_recipe(producers), {"mill": (4.0, 15.0), "bakery": (2.0, 2.0)})


class MadeByRecipe(unittest.TestCase):
    def test_only_goods_several_recipes_make_and_a_recipe_with_no_runs_at_nothing(self):
        outputs = {"wheel": {"power": 100.0}, "muscle": {"power": 1.0}, "bakery": {"bread": 3.0}}
        self.assertEqual(made_by_recipe({"muscle": (50.0, 60.0), "bakery": (2.0, 2.0)}, outputs),
                         {"power": {"muscle": 50.0, "wheel": 0.0}})


class ValueByGood(unittest.TestCase):
    def test_goods_with_no_price_or_no_quantity_are_left_out(self):
        self.assertEqual(value_by_good({"grain": 4.0, "odd": 3.0, "ale": 0.0}, {"grain": 0.5, "ale": 2.0}), {"grain": 2.0})


class StockByGood(unittest.TestCase):
    def test_a_goods_quantity_is_summed_over_agents_and_tiles(self):
        self.assertEqual(stock_by_good([{"grain": {"a": 1.0, "b": 2.0}}, {"grain": {"a": 4.0}, "ale": {"b": 1.0}}]),
                         {"grain": 7.0, "ale": 1.0})


ROWS = [{"stage": "first", "year": 0, "real_output": 10.0}, {"stage": "first", "year": 1, "real_output": 7.0},
        {"stage": "first", "year": 2, "real_output": 9.0}, {"stage": "trimmed", "year": 0, "real_output": 6.0}]


class Trough(unittest.TestCase):
    def test_the_first_stage_year_with_the_least_output(self):
        self.assertIs(trough(ROWS), ROWS[1])

    def test_no_first_stage_row_gives_none(self):
        self.assertIsNone(trough(ROWS[3:]))


class MarkedRows(unittest.TestCase):
    def test_first_year_trough_and_last_year(self):
        self.assertEqual(marked_rows(ROWS), [("first year", ROWS[0]), ("trough (first 1)", ROWS[1]), ("last year", ROWS[3])])

    def test_a_trough_in_the_first_year_is_not_listed_twice(self):
        rows = [dict(ROWS[1]), dict(ROWS[0])]
        self.assertEqual([label for label, _row in marked_rows(rows)], ["first year", "last year"])

    def test_no_rows_mark_nothing(self):
        self.assertEqual(marked_rows([]), [])


class LargestFirst(unittest.TestCase):
    def test_the_keys_largest_in_any_mix_first_with_none_where_a_mix_lacks_one(self):
        mixes = [{"output_by_good": {"grain": 5.0, "ale": 1.0}}, {"output_by_good": {"grain": 2.0, "cloth": 9.0}}]
        self.assertEqual(largest_first(mixes, "output_by_good", 2), [("cloth", [None, 9.0]), ("grain", [5.0, 2.0])])

    def test_a_size_reads_a_figure_of_several_parts(self):
        mixes = [{"hours_by_trade": {"farmer": (1.0, 9.0), "mason": (5.0, 0.0)}}]
        table = largest_first(mixes, "hours_by_trade", 1, size=lambda hours: hours[0] + hours[1])
        self.assertEqual(table, [("farmer", [(1.0, 9.0)])])


class RecipeShares(unittest.TestCase):
    def test_each_recipes_share_of_a_good_and_a_good_nothing_made_left_out(self):
        self.assertEqual(recipe_shares({"power": {"wheel": 30.0, "muscle": 10.0}, "glass": {"a": 0.0, "b": 0.0}}),
                         {"power": {"wheel": 0.75, "muscle": 0.25}})


class RecipesThatMoved(unittest.TestCase):
    def test_goods_whose_split_moved_most_first_and_a_split_that_stayed_left_out(self):
        mixes = [{"made_by_recipe": {"power": {"wheel": 90.0, "muscle": 10.0}, "iron": {"bloomery": 5.0, "blast": 5.0},
                                     "silver": {"lead": 6.0, "jarosite": 4.0}}},
                 {"made_by_recipe": {"power": {"wheel": 10.0, "muscle": 90.0}, "iron": {"bloomery": 5.0, "blast": 5.0},
                                     "silver": {"lead": 9.0, "jarosite": 1.0}}}]
        table = recipes_that_moved(mixes, 5)
        self.assertEqual([good for good, _rows in table], ["power", "silver"])
        self.assertEqual(table[0][1], [("muscle", [0.1, 0.9]), ("wheel", [0.9, 0.1])])

    def test_a_good_not_made_in_one_year_shows_none_there(self):
        mixes = [{"made_by_recipe": {"power": {"wheel": 0.0, "muscle": 0.0}}}, {"made_by_recipe": {"power": {"wheel": 1.0, "muscle": 0.0}}},
                 {"made_by_recipe": {"power": {"wheel": 0.0, "muscle": 1.0}}}]
        self.assertEqual(recipes_that_moved(mixes, 5), [("power", [("muscle", [None, 0.0, 1.0]), ("wheel", [None, 1.0, 0.0])])])


class MedianByGood(unittest.TestCase):
    def test_each_figures_median_over_the_members_that_have_it(self):
        tables = [{"bread": {"move": 0.1, "part": None}}, {"bread": {"move": 0.3, "part": 0.02}}, {"bread": {"move": 0.2, "part": 0.04}},
                  {"cart": {"move": 0.5, "part": None}}]
        medians = median_by_good(tables)
        self.assertAlmostEqual(medians["bread"]["move"], 0.2)
        self.assertAlmostEqual(medians["bread"]["part"], 0.03)
        self.assertEqual(medians["cart"], {"move": 0.5, "part": None})


if __name__ == "__main__":
    unittest.main()
