"""`price_kind_kernels.kinds_by_good` (one pass over the goods table's columns) and `price_kinds_of_goods` (the names and order), each
called on a few written-out markets, under numba and ROME_NO_JIT=1."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.economy.market_table_specs import GOODS_MARKETS, HELD_QUOTE_KIND, HELD_TRADE_AGE, GoodsMarkets
from sim.economy.market_tables import MarketTables
from sim.economy.price_kind_kernels import (NO_KIND, OPENING_ESTIMATE, REMEMBERED, SMOOTHED_TRADE, kinds_by_good, price_kinds_of_goods)

NAN = numpy.nan


def goods_markets(rows: int):
    table = GOODS_MARKETS.new_table(GoodsMarkets, rows, rows)
    for column in ("price", "usual_price", "cleared_price", "volume_weight"):
        getattr(table, column)[:] = NAN
    return table


class KindsByGoodTests(unittest.TestCase):
    def test_a_good_with_no_priced_market_has_no_kind(self):
        markets = goods_markets(2)
        markets.first[:] = [0, 0]
        markets.price[:] = [NAN, NAN]
        self.assertEqual(kinds_by_good(markets, numpy.array([0]), 2).tolist(), [NO_KIND, NO_KIND])

    def test_a_traded_market_wins_over_an_earlier_quote_whatever_the_order_of_rows(self):
        markets = goods_markets(3)
        markets.first[:] = [0, 0, 0]
        markets.area[:] = [0, 1, 2]
        markets.price[:] = [1.0, 2.0, 3.0]
        markets.held[:] = [HELD_QUOTE_KIND, HELD_TRADE_AGE, HELD_QUOTE_KIND]
        markets.trade_age[:] = [0, 0, 0]
        markets.quote_kind[:] = [3, 0, 4]
        self.assertEqual(kinds_by_good(markets, numpy.array([0, 1, 2]), 1).tolist(), [SMOOTHED_TRADE])

    def test_without_a_trade_the_lowest_ranked_area_decides_not_the_first_row(self):
        markets = goods_markets(3)
        markets.first[:] = [0, 0, 0]
        markets.area[:] = [0, 1, 2]
        markets.price[:] = [1.0, 2.0, 3.0]
        markets.held[:] = [HELD_QUOTE_KIND, HELD_QUOTE_KIND, HELD_QUOTE_KIND]
        markets.quote_kind[:] = [3, 4, 5]
        self.assertEqual(kinds_by_good(markets, numpy.array([2, 0, 1]), 1).tolist(), [4])

    def test_an_old_trade_is_remembered_and_no_trade_and_no_quote_is_the_opening_estimate(self):
        markets = goods_markets(3)
        markets.first[:] = [0, 1, 2]
        markets.price[:] = [1.0, 2.0, NAN]
        markets.held[:] = [HELD_TRADE_AGE, 0, HELD_TRADE_AGE]
        markets.trade_age[:] = [2, 0, 0]
        self.assertEqual(kinds_by_good(markets, numpy.array([0]), 3).tolist(), [REMEMBERED, OPENING_ESTIMATE, NO_KIND])


class PriceKindsOfGoodsTests(unittest.TestCase):
    def test_goods_come_in_the_order_of_their_sorted_market_names_and_kinds_by_name(self):
        tables = MarketTables()
        tables.admit_goods_markets(["iron_ore|north", "iron|south", "iron|north", "grain|north"])
        tables.kind_number("ask")
        table = tables.goods_table
        for key in ("iron_ore|north", "iron|north", "grain|north"):
            row = tables.goods_numbers[key]
            table.price[row] = 1.0
        table.held[tables.goods_numbers["iron|north"]] = HELD_QUOTE_KIND
        table.quote_kind[tables.goods_numbers["iron|north"]] = 0
        table.held[tables.goods_numbers["grain|north"]] = HELD_TRADE_AGE
        found = price_kinds_of_goods(tables, "traded", "old", "estimate")
        self.assertEqual((list(found.items())), [("grain", "traded"), ("iron_ore", "estimate"), ("iron", "ask")])      # "_" sorts before "|"


if __name__ == "__main__":
    unittest.main()
