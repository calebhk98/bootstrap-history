"""The goods record's per-market stores as columns (`goods_market_column.MarketColumn`) answer as the dictionaries they replaced."""

QUICK_TOPIC = True

import unittest

import numpy as np

from sim.compiled_tables.ids import IdTable
from sim.economy.goods_market_column import MarketColumn
from sim.economy.market_tables import MarketTables


class MarketColumnTests(unittest.TestCase):
    def test_it_answers_as_the_dict_of_the_same_keys(self):
        column = MarketColumn(items={"grain|a1": 2.0, "salt|a0": 3.5})
        self.assertEqual(column, {"grain|a1": 2.0, "salt|a0": 3.5})
        self.assertEqual(column.get("grain|a1"), 2.0)
        self.assertIsNone(column.get("grain|a0"))
        self.assertEqual(column.get("grain|a0", 9.0), 9.0)
        self.assertIn("salt|a0", column)
        self.assertEqual(len(column), 2)
        self.assertEqual(sorted(column.items()), [("grain|a1", 2.0), ("salt|a0", 3.5)])

    def test_zero_is_a_figure_and_a_popped_key_is_absent(self):
        column = MarketColumn(items={"grain|a1": 0.0})
        self.assertIn("grain|a1", column)
        self.assertEqual(column.pop("grain|a1"), 0.0)
        self.assertNotIn("grain|a1", column)
        self.assertIsNone(column.pop("grain|a1", None))

    def test_an_integer_column_answers_whole_numbers(self):
        column = MarketColumn(items={"grain|a1": 3}, integer=True)
        self.assertIsInstance(column.get("grain|a1"), int)
        self.assertEqual(column.get("salt|a1", 0), 0)
        self.assertEqual(column.saved(), {"grain|a1": 3})

    def test_replace_rows_holds_exactly_those_figures(self):
        tables = MarketTables()
        column = MarketColumn(tables, {"grain|a1": 2.0, "salt|a0": 3.5})
        rows = column.rows_of(["salt|a0", "wool|a2"])
        column.replace_rows(rows, np.array([1.0, 0.0]))
        self.assertEqual(column, {"salt|a0": 1.0, "wool|a2": 0.0})

    def test_the_save_lists_names_in_order_and_hold_named_restores_it(self):
        column = MarketColumn(items={"salt|a0": 3.5, "grain|a1": 2.0})
        saved = column.saved()
        self.assertEqual(list(saved), ["grain|a1", "salt|a0"])
        loaded = MarketColumn(MarketTables())
        loaded.hold_named(list(saved), list(saved.values()))
        self.assertEqual(loaded, column)

    def test_follow_carries_the_figures_over_a_renumbering(self):
        tables = MarketTables()
        column = MarketColumn(tables, {"grain|a1": 2.0, "salt|a0": 3.5})
        self.assertEqual(tables.goods_numbers["grain|a1"], 0)      # grain|a1 is row 0, salt|a0 row 1
        numbering = IdTable("goods market")
        numbering.admit(["grain|b1", "salt|a0"])     # a redraw: grain|a1 is dropped, grain|b1 takes its figure
        tables.install_goods_markets(numbering, tables.blank_goods_table(numbering))
        column.follow(np.array([-1, 1], dtype=np.int64), np.array([0], dtype=np.int64), np.array([0], dtype=np.int64))
        self.assertEqual(column, {"salt|a0": 3.5, "grain|b1": 2.0})

    def test_iteration_is_in_good_then_area_order_whatever_the_numbering(self):
        column = MarketColumn(items={"iron_ore|a0": 1.0, "iron|b0": 2.0, "iron|a1": 3.0})
        self.assertEqual(list(column), ["iron|a1", "iron|b0", "iron_ore|a0"])
        self.assertEqual(list(column.items())[0], ("iron|a1", 3.0))

    def test_get_many_gives_the_default_for_a_market_with_no_figure(self):
        column = MarketColumn(items={"grain|a1": 2.0, "salt|a0": 0.0})
        self.assertEqual(column.get_many(["salt|a0", "wool|a9", "grain|a1"], 7.0), [0.0, 7.0, 2.0])
        streaks = MarketColumn(items={"grain|a1": 3}, integer=True)
        self.assertEqual(streaks.get_many(["grain|a1", "salt|a0"], 0), [3, 0])

    def test_copy_is_independent(self):
        column = MarketColumn(items={"grain|a1": 2.0})
        copied = column.copy()
        copied["grain|a1"] = 5.0
        self.assertEqual(column["grain|a1"], 2.0)


if __name__ == "__main__":
    unittest.main()


class MarketColumnOrderTests(unittest.TestCase):
    def test_items_and_iteration_match_the_sorted_names_of_random_columns(self):
        import random
        from sim.tests.goods_market_column_plain import items_by_sorting
        goods = ["iron", "iron_ore", "iron2", "salt", "grain", "a b"]
        for seed in range(40):
            generator = random.Random(seed)
            names = ["%s|%s" % (generator.choice(goods), generator.choice(["a0", "a1", "a10", "b", "a"])) for _ in range(generator.randint(0, 30))]
            figures = {name: float(generator.randint(0, 9)) for name in names}
            for integer in (False, True):
                column = MarketColumn(MarketTables(), figures, integer=integer)
                expected = items_by_sorting(list(column.named()[0]), column.named()[1], integer)
                self.assertEqual(column.items(), expected)
                self.assertEqual(list(column), [name for name, _figure in expected])
