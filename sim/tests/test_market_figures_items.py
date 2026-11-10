"""`items` of the merchant and goods-record figure columns is one pass over the column and equals the per-key reads."""
import unittest

from sim.economy.goods_market_column import MarketColumn
from sim.economy.merchant_figures import MarketFigures

QUICK_TOPIC = True


class MarketFiguresItems(unittest.TestCase):
    def test_items_are_the_figures_of_each_key_in_iteration_order(self):
        figures = MarketFigures(items={("salt", "a0"): 3.5, ("grain", "a1"): 2.0, ("wool", "a0"): 0.0})
        self.assertEqual(figures.items(), [(key, figures[key]) for key in figures])

    def test_a_removed_market_is_not_listed(self):
        figures = MarketFigures(items={("salt", "a0"): 3.5, ("grain", "a1"): 2.0})
        figures.pop(("salt", "a0"))
        self.assertEqual(figures.items(), [(("grain", "a1"), 2.0)])


class MarketColumnItems(unittest.TestCase):
    def test_items_are_in_good_then_area_order_not_numbering_order(self):
        column = MarketColumn(items={"salt|a0": 3.5, "grain|a1": 2.0, "grain|a0": 1.0, "grain-x|a0": 4.0})
        self.assertEqual(column.items(), [(key, column[key]) for key in column])
        self.assertEqual([key for key, _figure in column.items()], ["grain|a0", "grain|a1", "grain-x|a0", "salt|a0"])

    def test_an_integer_column_gives_whole_numbers(self):
        column = MarketColumn(items={"grain|a1": 3, "salt|a0": 1}, integer=True)
        self.assertEqual(column.items(), [("grain|a1", 3), ("salt|a0", 1)])
        self.assertIs(type(column.items()[0][1]), int)


if __name__ == "__main__":
    unittest.main()
