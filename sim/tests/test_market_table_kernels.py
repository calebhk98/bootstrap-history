"""The market memory's table kernels, each called on a few written-out rows (under numba and ROME_NO_JIT=1)."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.economy.market_table_kernels import (KIND_BARE, KIND_OFFERED, NAN_VALUE, bare_quotes, drop_counts, drop_floats,
                                              market_of_good_tile, markets_traded_within, note_year_traded, offered_prices,
                                              put_counts, put_floats, remap_goods_markets, scatter_flags, scatter_values)
from sim.economy.market_table_specs import (GOODS_MARKETS, HELD_QUOTE_KIND, HELD_TRADE_AGE, HELD_YEARS_WITHOUT_BIDS, PRICES,
                                            STORE_COUNT, TRADE_AGE, GoodsMarkets)

NAN = numpy.nan


def goods_markets(rows: int):
    """A blank goods table of `rows` markets: NaN where a figure is missing, nothing held."""
    table = GOODS_MARKETS.new_table(GoodsMarkets, rows, rows)
    for column in ("price", "usual_price", "cleared_price", "volume_weight"):
        getattr(table, column)[:] = NAN
    return table


def bookkeeping():
    return numpy.zeros(STORE_COUNT, dtype=numpy.int64), numpy.zeros(STORE_COUNT, dtype=numpy.int64)


class PutAndDropTests(unittest.TestCase):
    def test_put_floats_gives_new_markets_entry_numbers_in_the_order_given(self):
        values, order = numpy.full(4, NAN), numpy.zeros(4, dtype=numpy.int64)
        next_order, member_count = bookkeeping()
        code = put_floats(values, order, next_order, member_count, PRICES, numpy.array([2, 0]), numpy.array([5.0, 6.0]))
        self.assertEqual((code, values[[0, 2]].tolist(), order[[2, 0]].tolist(), next_order[PRICES], member_count[PRICES]),
                         (0, [6.0, 5.0], [0, 1], 2, 2))

    def test_put_floats_over_a_member_keeps_its_entry_number(self):
        values, order = numpy.array([1.0, NAN]), numpy.array([7, 0])
        next_order, member_count = bookkeeping()
        next_order[PRICES], member_count[PRICES] = 8, 1
        put_floats(values, order, next_order, member_count, PRICES, numpy.array([0]), numpy.array([2.0]))
        self.assertEqual((values[0], order[0], next_order[PRICES], member_count[PRICES]), (2.0, 7, 8, 1))

    def test_put_floats_refuses_a_nan_figure_with_its_cause_and_writes_nothing_after_it(self):
        values, order = numpy.full(3, NAN), numpy.zeros(3, dtype=numpy.int64)
        next_order, member_count = bookkeeping()
        code = put_floats(values, order, next_order, member_count, PRICES, numpy.array([0, 1, 2]), numpy.array([1.0, NAN, 3.0]))
        self.assertEqual((code, numpy.isnan(values).tolist(), member_count[PRICES]), (NAN_VALUE, [False, True, True], 1))

    def test_drop_floats_uncounts_only_members(self):
        values = numpy.array([1.0, NAN])
        next_order, member_count = bookkeeping()
        member_count[PRICES] = 1
        drop_floats(values, member_count, PRICES, numpy.array([0, 1]))
        self.assertEqual((numpy.isnan(values).tolist(), member_count[PRICES]), ([True, True], 0))

    def test_put_counts_sets_the_held_bit_and_enters_once(self):
        values, held = numpy.zeros(3, dtype=numpy.int64), numpy.zeros(3, dtype=numpy.int64)
        order = numpy.zeros(3, dtype=numpy.int64)
        next_order, member_count = bookkeeping()
        put_counts(values, held, order, next_order, member_count, TRADE_AGE, HELD_TRADE_AGE, numpy.array([1, 1]), numpy.array([4, 5]))
        self.assertEqual((values.tolist(), held.tolist(), order[1], next_order[TRADE_AGE], member_count[TRADE_AGE]),
                         ([0, 5, 0], [0, HELD_TRADE_AGE, 0], 0, 1, 1))

    def test_drop_counts_clears_only_its_bit(self):
        held = numpy.array([HELD_TRADE_AGE | HELD_YEARS_WITHOUT_BIDS])
        next_order, member_count = bookkeeping()
        member_count[TRADE_AGE] = 1
        drop_counts(held, member_count, TRADE_AGE, HELD_TRADE_AGE, numpy.array([0]))
        self.assertEqual((held.tolist(), member_count[TRADE_AGE]), ([HELD_YEARS_WITHOUT_BIDS], 0))


class AgeTests(unittest.TestCase):
    def test_note_year_traded_ages_the_old_markets_and_zeroes_the_traded_ones_in_order(self):
        markets = goods_markets(3)
        markets.held[:] = [HELD_TRADE_AGE, 0, 0]
        markets.trade_age[:] = [4, 0, 0]
        markets.order_trade_age[0] = 0
        next_order, member_count = bookkeeping()
        next_order[TRADE_AGE], member_count[TRADE_AGE] = 1, 1
        note_year_traded(markets, numpy.array([2, 1]), next_order, member_count)
        self.assertEqual((markets.trade_age.tolist(), markets.held.tolist(), markets.order_trade_age.tolist(), member_count[TRADE_AGE]),
                         ([5, 0, 0], [HELD_TRADE_AGE] * 3, [0, 2, 1], 3))

    def test_note_year_traded_resets_a_market_that_had_an_age(self):
        markets = goods_markets(1)
        markets.held[0], markets.trade_age[0] = HELD_TRADE_AGE, 3
        next_order, member_count = bookkeeping()
        note_year_traded(markets, numpy.array([0]), next_order, member_count)
        self.assertEqual((markets.trade_age[0], member_count[TRADE_AGE]), (0, 0))

    def test_markets_traded_within_needs_an_age_at_most_the_years(self):
        markets = goods_markets(3)
        markets.held[:] = [HELD_TRADE_AGE, HELD_TRADE_AGE, 0]
        markets.trade_age[:] = [1, 3, 0]
        self.assertEqual(markets_traded_within(markets, 2).tolist(), [True, False, False])


class ReadTests(unittest.TestCase):
    CLASS_OF_KIND = numpy.array([KIND_OFFERED | KIND_BARE, KIND_BARE, KIND_OFFERED], dtype=numpy.int64)    # ask, bid ceiling, estimate

    def five_markets(self):
        """traded last year; an ask after an old trade; a bid ceiling; no kind and no age (opening estimate); no kind but an old age."""
        markets = goods_markets(6)
        markets.price[:5] = [1.0, 2.0, 3.0, 4.0, 5.0]
        markets.held[:] = [HELD_TRADE_AGE, HELD_TRADE_AGE | HELD_QUOTE_KIND, HELD_QUOTE_KIND, 0, HELD_TRADE_AGE, 0]
        markets.trade_age[:] = [0, 2, 0, 0, 2, 0]
        markets.quote_kind[:] = [1, 0, 1, 0, 0, 0]
        return markets

    def test_offered_prices_follow_price_kind(self):
        offered = offered_prices(self.five_markets(), self.CLASS_OF_KIND)
        self.assertEqual(numpy.nan_to_num(offered, nan=-1.0).tolist(), [1.0, 2.0, -1.0, 4.0, -1.0, -1.0])

    def test_bare_quotes_are_untraded_asks_and_bids(self):
        self.assertEqual(bare_quotes(self.five_markets(), self.CLASS_OF_KIND).tolist(), [False, True, True, False, False, False])

    def test_scatter_values_skips_nan_and_markets_without_a_cell(self):
        grid = numpy.full((2, 2), NAN)
        scatter_values(grid, numpy.array([1.0, NAN, 3.0, 4.0]), numpy.array([0, 1, -1, 1]), numpy.array([1, 0, 0, 1]), 4)
        self.assertEqual(numpy.nan_to_num(grid, nan=-1.0).tolist(), [[-1.0, 1.0], [-1.0, 4.0]])

    def test_scatter_flags_sets_the_cells_of_flagged_markets(self):
        grid = numpy.zeros((2, 2), dtype=numpy.bool_)
        scatter_flags(grid, numpy.array([True, False, True]), numpy.array([0, 1, -1]), numpy.array([0, 1, 0]), 3)
        self.assertEqual(grid.tolist(), [[True, False], [False, False]])

    def test_market_of_good_tile_looks_up_each_tiles_area_column(self):
        area_of_good_tile = numpy.array([[0, 1, -1], [1, 1, 0]], dtype=numpy.int64)
        market_of_good_area = numpy.array([[5, 6], [-1, 8]], dtype=numpy.int64)
        self.assertEqual(market_of_good_tile(area_of_good_tile, market_of_good_area).tolist(), [[5, 6, -1], [8, 8, -1]])


class RemapTests(unittest.TestCase):
    def test_survivors_keep_their_entry_numbers_and_pairs_enter_after_them(self):
        old = goods_markets(3)
        old.price[:] = [10.0, 20.0, 30.0]
        old.order_price[:] = [1, 0, 2]
        old.held[1] = HELD_TRADE_AGE
        old.trade_age[1] = 6
        new = goods_markets(4)
        next_order, member_count = bookkeeping()
        next_order[PRICES], next_order[TRADE_AGE] = 3, 1
        # old market 0 survives as new 1; old 1 is dropped but feeds new 0 and new 3; old 2 is dropped and feeds new 2
        remap_goods_markets(old, new, numpy.array([1, -1, -1]), numpy.array([0, 3, 2]), numpy.array([1, 1, 2]), next_order, member_count)
        self.assertEqual((new.price.tolist(), new.order_price.tolist(), member_count[PRICES], next_order[PRICES]),
                         ([20.0, 10.0, 30.0, 20.0], [3, 1, 5, 4], 4, 6))
        self.assertEqual((new.trade_age[[0, 3]].tolist(), new.held.tolist(), member_count[TRADE_AGE]),
                         ([6, 6], [HELD_TRADE_AGE, 0, 0, HELD_TRADE_AGE], 2))

    def test_a_pair_over_a_market_already_in_the_store_overwrites_it_in_place(self):
        old = goods_markets(2)
        old.price[:] = [1.0, 2.0]
        old.order_price[:] = [0, 1]
        new = goods_markets(1)
        next_order, member_count = bookkeeping()
        next_order[PRICES] = 2
        remap_goods_markets(old, new, numpy.array([0, -1]), numpy.array([0]), numpy.array([1]), next_order, member_count)
        self.assertEqual((new.price[0], new.order_price[0], member_count[PRICES], next_order[PRICES]), (2.0, 0, 1, 2))

    def test_a_pair_from_a_market_never_numbered_changes_nothing(self):
        old = goods_markets(1)
        new = goods_markets(1)
        next_order, member_count = bookkeeping()
        remap_goods_markets(old, new, numpy.array([-1]), numpy.array([0]), numpy.array([-1]), next_order, member_count)
        self.assertEqual((numpy.isnan(new.price[0]), member_count[PRICES]), (True, 0))


if __name__ == "__main__":
    unittest.main()
