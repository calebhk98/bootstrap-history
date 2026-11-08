"""The year's table of goods-market figures (`goods_year_markets.YearMarkets`): rows are claimed and filled, the respend's totals are
added to the cleared rows only, unsold is what the last round left on offer and never below zero."""

QUICK_TOPIC = True

import math
import unittest

import numpy as np

from sim.economy.goods_year_markets import YearMarkets


def three_markets() -> YearMarkets:
    markets = YearMarkets(2)         # a small table, so claiming the rows grows it
    first = markets.claim(3)
    markets.fill(first, [1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0], [1.0, 2.0, 12.0], [0, 1, 2], [math.nan, 1.5, 2.5])
    return markets


class YearMarketsTests(unittest.TestCase):
    def test_claim_grows_the_table_and_counts_the_rows(self):
        markets = YearMarkets(2)
        self.assertEqual(markets.claim(3), 0)
        self.assertEqual(markets.claim(2), 3)
        self.assertEqual(int(markets.table.row_count[0]), 5)
        self.assertGreaterEqual(int(markets.table.capacity[0]), 5)

    def test_fill_sets_the_cells_and_a_missing_price_is_nan(self):
        table = three_markets().table
        self.assertEqual(table.delivered[:3].tolist(), [1.0, 2.0, 3.0])
        self.assertEqual(table.idle_years[:3].tolist(), [0, 1, 2])
        self.assertTrue(math.isnan(table.last_price[0]))
        self.assertEqual(table.last_price[1], 1.5)

    def test_add_rounds_changes_only_the_rows_it_names(self):
        markets = three_markets()
        markets.add_rounds(np.array([2, 0], dtype=np.int64), np.array([0.5, 0.25]), np.array([1.0, 2.0]), np.array([10.0, 11.0]),
                           np.array([0.5, 0.25]))
        table = markets.table
        self.assertEqual(table.delivered[:3].tolist(), [1.25, 2.0, 3.5])
        self.assertEqual(table.wanted[:3].tolist(), [6.0, 5.0, 7.0])
        self.assertEqual(table.last_offered[:3].tolist(), [11.0, 8.0, 10.0])
        self.assertEqual(table.last_delivered[:3].tolist(), [0.25, 2.0, 0.5])

    def test_unsold_is_what_the_last_round_left_and_never_below_zero(self):
        markets = three_markets()
        self.assertEqual(markets.unsold(np.array([0, 1, 2], dtype=np.int64)).tolist(), [6.0, 6.0, 0.0])


if __name__ == "__main__":
    unittest.main()
