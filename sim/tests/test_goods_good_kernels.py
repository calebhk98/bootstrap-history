"""The per-good kernels of the goods phase, each compared bit for bit with the chain of numpy calls it replaced (kept in
`goods_good_plain.py`), on inputs written out and on seeded random order tables with many ties. Each test calls one kernel."""
import math
import unittest

import numpy

from sim.compiled_tables.growth import reserve_rows
from sim.economy import goods_respend_settle_kernel, market_curves_kernel, market_curves_rows
from sim.economy import goods_batch_write_kernel, goods_clearing_kernel, goods_decide_inputs_kernel, goods_pack_kernel, goods_rows_kernel, stable_order_kernel
from sim.economy.goods_order_tables import (BID_ORDER, GOODS_MARKET_RESULTS, GOODS_OFFERS, GOODS_PAIRS, OFFER_ORDER, BidOrder,
                                            GoodsMarketResults, GoodsPairs, OfferOrder)
from sim.tests import goods_good_plain as plain
from sim.tests.market_curves_plain import plain_summarize_columns
from sim.tests.respend_plain import plain_settlement_by_good

SEEDS = range(40)


def same(case, got, expected):
    """Each array of the two tuples equal in value, dtype and shape (NaN equal to NaN)."""
    case.assertEqual(len(got), len(expected))
    for place, (found, wanted) in enumerate(zip(got, expected)):
        found, wanted = numpy.asarray(found), numpy.asarray(wanted)
        case.assertEqual(found.shape, wanted.shape, place)
        case.assertEqual(found.dtype.kind, wanted.dtype.kind, place)
        case.assertTrue(numpy.array_equal(found, wanted, equal_nan=found.dtype.kind == "f"), (place, found, wanted))


def copy_table(table):
    return type(table)(*[each.copy() for each in table])


class StableOrderIsLexsort(unittest.TestCase):

    def test_successive_stable_sorts_order_ties_as_lexsort_does(self):
        for seed in SEEDS:
            generator = numpy.random.default_rng(seed)
            keys = tuple(generator.integers(0, 3, 40).astype(numpy.int64) for _ in range(4))
            got = stable_order_kernel.stable_order(keys)
            self.assertEqual(got.tolist(), numpy.lexsort(keys).tolist())


class GoodRowsFindsTheGoodsMarkets(unittest.TestCase):

    def test_written_out(self):
        bids, offers = plain.random_tables(numpy.random.default_rng(3), 0, 0)
        bids.good[:3], bids.market[:3], bids.budget[:3], bids.row_count[0] = [1, 0, 1], [4, 4, 2], [1.0, 0.0, 0.0], 3
        offers.good[:2], offers.market[:2], offers.quantity[:2], offers.seller[:2], offers.row_count[0] = [1, 1], [2, 5], [2.0, 0.0], [0, 1], 2
        market_area = numpy.array([0, 1, 2, 3, 4, 5], dtype=numpy.int64)
        area_rank = numpy.array([5, 4, 3, 2, 1, 0], dtype=numpy.int64)
        got = goods_rows_kernel.good_rows(bids, offers, 1, market_area, area_rank, numpy.zeros(2, dtype=numpy.int64), True)
        self.assertEqual(got[0].tolist(), [5, 4, 2])                     # clearing order: rank 0 (market 5), then 4, then market 2... by area rank
        self.assertEqual((got[1].tolist(), got[3].tolist()), ([0, 2], [0, 1]))
        self.assertEqual(got[9].tolist(), [False, False, True])           # only market 2 has units
        self.assertEqual((got[10].tolist(), got[11].tolist(), got[12].tolist()), ([True, False, True], [False, False, True], [False, True, False]))

    def test_random_tables_with_ties(self):
        for seed in SEEDS:
            generator = numpy.random.default_rng(seed)
            bids, offers = plain.random_tables(generator, int(generator.integers(0, 30)), int(generator.integers(0, 30)))
            market_area = generator.integers(0, 4, 6).astype(numpy.int64)
            area_rank = generator.permutation(4).astype(numpy.int64)
            is_edge = (generator.integers(0, 5, 5) == 0).astype(numpy.int64)
            for good_id in range(3):
                for batchable in (True, False):
                    same(self, goods_rows_kernel.good_rows(bids, offers, good_id, market_area, area_rank, is_edge, batchable),
                         plain.plain_good_rows(bids, offers, good_id, market_area, area_rank, is_edge, batchable))


class PackArraysPacksTheBatch(unittest.TestCase):

    def test_random_tables_with_ties(self):
        for seed in SEEDS:
            generator = numpy.random.default_rng(seed)
            bids, offers = plain.random_tables(generator, int(generator.integers(1, 40)), int(generator.integers(1, 40)))
            market_area = generator.integers(0, 4, 6).astype(numpy.int64)
            rows = plain.plain_good_rows(bids, offers, 1, market_area, generator.permutation(4).astype(numpy.int64),
                                         numpy.zeros(5, dtype=numpy.int64), True)
            markets, flags = rows[0], generator.integers(0, 3, len(rows[0])) > 0
            if not flags.any():
                continue
            ranks = [generator.permutation(5).astype(numpy.int64), generator.permutation(5).astype(numpy.int64), generator.permutation(4).astype(numpy.int64)]
            volume = generator.integers(1, 9, 6) * 0.5
            price = numpy.where(generator.integers(0, 3, 6) == 0, numpy.nan, generator.integers(1, 9, 6) * 0.25)
            unmet = numpy.where(generator.integers(0, 3, 6) == 0, numpy.nan, generator.integers(0, 5, 6) * 0.5)
            rates = generator.integers(1, 9, 4) * 0.01
            arguments = (bids, offers, rows[3], rows[4], rows[1], rows[2], flags, markets, ranks[0], ranks[1], ranks[2], price, volume,
                         market_area, unmet, rates)
            got = goods_pack_kernel.pack_arrays(*arguments, numpy.ones(4, dtype=numpy.bool_), 0.25)
            self.assertEqual(got[-2], 0)
            same(self, got[:-2], plain.plain_pack(*arguments, 0.25))

    def test_an_area_without_a_rate_is_reported(self):
        generator = numpy.random.default_rng(1)
        bids, offers = plain.random_tables(generator, 6, 6)
        market_area = numpy.array([0, 1, 2, 3, 0, 1], dtype=numpy.int64)
        rows = plain.plain_good_rows(bids, offers, 0, market_area, numpy.arange(4, dtype=numpy.int64), numpy.zeros(5, dtype=numpy.int64), True)
        flags = numpy.ones(len(rows[0]), dtype=bool)
        known = numpy.ones(4, dtype=numpy.bool_)
        known[market_area[rows[0][0]]] = False
        got = goods_pack_kernel.pack_arrays(bids, offers, rows[3], rows[4], rows[1], rows[2], flags, rows[0], numpy.arange(5, dtype=numpy.int64),
                                            numpy.arange(5, dtype=numpy.int64), numpy.arange(4, dtype=numpy.int64), numpy.ones(6),
                                            numpy.ones(6), market_area, numpy.zeros(6), numpy.zeros(4), known, 0.25)
        self.assertEqual((got[-2], numpy.flatnonzero(got[-1]).tolist()), (1, [market_area[rows[0][0]]]))
        self.assertTrue(math.isnan(got[17][0]))


class DecideInputsGathersTheSellersFigures(unittest.TestCase):

    def test_random_tables(self):
        for seed in SEEDS:
            generator = numpy.random.default_rng(seed)
            _bids, offers = plain.random_tables(generator, 0, int(generator.integers(1, 30)), agents=6)
            count = int(offers.row_count[0])
            offer_rows = generator.permutation(count)[:max(1, count - 2)].astype(numpy.int64)
            producer_row_of_agent = generator.integers(-1, 4, 6).astype(numpy.int64)
            recipe_row = generator.integers(0, 3, 4).astype(numpy.int64)
            slot_of = generator.integers(-1, 2, (3, 5)).astype(numpy.int64)
            arguments = (offers, offer_rows, producer_row_of_agent, recipe_row, generator.integers(1, 4, 4), generator.random(4),
                         generator.random(4) + 0.5, slot_of, 2, generator.random((4, 2)), generator.random((4, 2)), generator.random((4, 2)),
                         generator.random((3, 5)), generator.random(4) + 1.0)
            offer_ptr = numpy.array([0, 1, len(offer_rows)], dtype=numpy.int64)
            got = goods_decide_inputs_kernel.decide_inputs(offer_rows, offer_ptr, *arguments[:1], *arguments[2:], 0.125)
            self.assertEqual(got[-2], 0)
            same(self, got[:-2], plain.plain_decide_inputs(offers, offer_rows, *arguments[2:], numpy.zeros(2), 0.125))

    def test_a_tile_without_a_band_multiple_is_reported(self):
        _bids, offers = plain.random_tables(numpy.random.default_rng(2), 0, 3)
        offers.tile[:3] = [1, 0, 1]
        multiples = numpy.array([1.5, numpy.nan, 2.0, 2.0])
        got = goods_decide_inputs_kernel.decide_inputs(
            numpy.array([0, 1, 2], dtype=numpy.int64), numpy.array([0, 3], dtype=numpy.int64), offers, numpy.full(5, -1, dtype=numpy.int64),
            numpy.zeros(1, dtype=numpy.int64), numpy.ones(1), numpy.ones(1), numpy.ones(1), numpy.zeros((1, 1), dtype=numpy.int64), 0,
            numpy.ones((1, 1)), numpy.ones((1, 1)), numpy.ones((1, 1)), numpy.ones((1, 1)), multiples, 0.0)
        self.assertEqual((got[-2], numpy.flatnonzero(got[-1]).tolist()), (1, [1]))


class ClearingColumnsFillsTheGoodsColumns(unittest.TestCase):

    def test_random_batches(self):
        for seed in SEEDS:
            generator = numpy.random.default_rng(seed)
            count = int(generator.integers(1, 7))
            flags = generator.integers(0, 2, count) > 0
            has_units = generator.integers(0, 3, count) > 0
            batched = int(flags.sum())
            offer_counts = generator.integers(0, 4, batched)
            batch_offer_ptr = numpy.concatenate(([0], numpy.cumsum(offer_counts))).astype(numpy.int64)
            total = int(batch_offer_ptr[-1])
            batch = dict(traded_flag=generator.integers(0, 2, batched) > 0, mean=generator.random(batched), traded=generator.random(batched),
                         requested=generator.random(batched), supply=generator.random(batched),
                         left=generator.integers(0, 3, total) * 0.5)
            pack_offer_rows = generator.permutation(total + 5)[:total].astype(numpy.int64)
            untraded = dict(lowest_ask=generator.integers(0, 4, count) * 1.0, lowest_clamped=generator.integers(0, 4, count) * 1.0,
                            supply=generator.random(count), wanted=generator.random(count), best_bid=generator.integers(0, 4, count) * 1.0,
                            funded=generator.integers(0, 2, count) > 0)
            for name in ("lowest_ask", "lowest_clamped", "best_bid"):
                untraded[name][untraded[name] == 0.0] = numpy.nan
            last_price = numpy.where(generator.integers(0, 3, count) == 0, numpy.nan, generator.integers(1, 4, count) * 1.0)
            group_counts = generator.integers(0, 4, count)
            offer_ptr = numpy.concatenate(([0], numpy.cumsum(group_counts))).astype(numpy.int64)
            offer_grouped = generator.permutation(int(offer_ptr[-1]) + 3)[:int(offer_ptr[-1])].astype(numpy.int64)
            offer_quantity = generator.integers(0, 3, len(offer_grouped) + 3) * 1.0
            arguments = (flags, has_units, last_price, batch["traded_flag"], batch["mean"], batch["traded"], batch["requested"],
                         batch["supply"], batch["left"], batch_offer_ptr, pack_offer_rows, untraded["lowest_ask"], untraded["lowest_clamped"],
                         untraded["supply"], untraded["wanted"], untraded["best_bid"], untraded["funded"], offer_grouped, offer_ptr,
                         numpy.zeros(int(offer_grouped.max(initial=0)) + 1) + 1.0)
            quantity_of_row = generator.integers(0, 3, int(offer_grouped.max(initial=0)) + 1) * 1.0
            arguments = arguments[:-1] + (quantity_of_row,)
            expected = plain.plain_clearing_columns(flags, has_units, last_price, batch, batch_offer_ptr, pack_offer_rows, untraded,
                                                    offer_grouped, offer_ptr, quantity_of_row)
            same(self, goods_clearing_kernel.clearing_columns(*arguments), expected)

    def test_no_batch_and_no_untraded_figures(self):
        empty_floats, empty_ints = numpy.zeros(0), numpy.zeros(0, dtype=numpy.int64)
        got = goods_clearing_kernel.clearing_columns(
            numpy.array([False, False]), numpy.array([True, True]), numpy.array([1.0, numpy.nan]), numpy.zeros(0, dtype=numpy.bool_),
            empty_floats, empty_floats, empty_floats, empty_floats, empty_floats, numpy.zeros(1, dtype=numpy.int64), empty_ints,
            empty_floats, empty_floats, empty_floats, empty_floats, empty_floats, numpy.zeros(0, dtype=numpy.bool_), empty_ints,
            numpy.zeros(3, dtype=numpy.int64), empty_floats)
        self.assertEqual(got[1].tolist(), [goods_clearing_kernel.ON_OBJECTS] * 2)
        self.assertEqual((len(got[9]), got[10].tolist(), got[11].tolist()), (0, [0, 0, 0], [0, 0]))


class CurveArraysSummariseAMarket(unittest.TestCase):

    def test_random_tables_with_ties(self):
        for seed in SEEDS:
            generator = numpy.random.default_rng(seed)
            bids, offers = plain.random_tables(generator, int(generator.integers(0, 30)), int(generator.integers(0, 30)))
            bid_rows = generator.permutation(int(bids.row_count[0]))[:int(generator.integers(0, 30))].astype(numpy.int64)
            offer_rows = generator.permutation(int(offers.row_count[0]))[:int(generator.integers(0, 30))].astype(numpy.int64)
            got = market_curves_rows._summary(market_curves_kernel.curve_arrays_of_rows(bids, offers, bid_rows, offer_rows, 0))
            expected = plain_summarize_columns(
                bids.floor_quantity[bid_rows], bids.flexible_quantity[bid_rows], bids.reference_price[bid_rows], bids.elasticity[bid_rows],
                bids.budget[bid_rows], bids.maximum_price[bid_rows], bids.buyer[bid_rows] == 0, offers.reservation_price[offer_rows],
                offers.quantity[offer_rows], offers.seller[offer_rows] == 0)
            self.assertEqual(got, expected, seed)


class SettlementByGoodSumsThePairs(unittest.TestCase):

    def test_written_out(self):
        item = numpy.array([1, 0, 1], dtype=numpy.int64)
        got = goods_respend_settle_kernel.settlement_by_good(
            item, numpy.array([0, 1, 0], dtype=numpy.int64), numpy.array([2, 2, 3], dtype=numpy.int64), numpy.array([0, 1, 0], dtype=numpy.int64),
            numpy.array([0, 0, 1], dtype=numpy.int64), numpy.array([1.0, 2.0, 4.0]), numpy.array([10.0, 20.0, 40.0]),
            numpy.array([5, 6, 7, 8], dtype=numpy.int64), numpy.array([7, 8], dtype=numpy.int64), numpy.array([0, 0], dtype=numpy.int64),
            numpy.array([5, 6], dtype=numpy.int64), numpy.array([0, 0], dtype=numpy.int64), 2)
        self.assertEqual(got[0].tolist(), [0, 1])
        self.assertEqual((got[2].tolist(), got[3].tolist(), got[4].tolist()), ([6, 7, 5, 7, 8], [20.0, 0.0, 50.0, 0.0, 0.0], [0.0, 20.0, 0.0, 10.0, 40.0]))
        self.assertEqual((got[6].tolist(), got[8].tolist(), got[9].tolist()), ([7, 6, 7, 8, 5], [2.0, 0.0, 1.0, 4.0, 0.0], [0.0, 2.0, 0.0, 0.0, 5.0]))

    def test_random_pairs_with_ties(self):
        for seed in SEEDS:
            generator = numpy.random.default_rng(seed)
            pairs, agents, keys, buyers, goods = int(generator.integers(1, 40)), 7, 6, 5, 4
            item = generator.integers(0, goods, pairs).astype(numpy.int64)
            arguments = (item, generator.integers(0, agents, pairs).astype(numpy.int64), generator.integers(0, agents, pairs).astype(numpy.int64),
                         generator.integers(0, buyers, pairs).astype(numpy.int64), generator.integers(0, keys, pairs).astype(numpy.int64),
                         generator.integers(1, 9, pairs) * 0.1, generator.integers(1, 9, pairs) * 0.3, generator.permutation(50)[:agents].astype(numpy.int64),
                         generator.permutation(8)[:keys].astype(numpy.int64), generator.integers(0, 3, keys).astype(numpy.int64),
                         generator.permutation(8)[:buyers].astype(numpy.int64), generator.integers(0, 3, buyers).astype(numpy.int64))
            got = goods_respend_settle_kernel.settlement_by_good(*arguments, goods)
            expected = plain_settlement_by_good(*arguments)
            self.assertEqual(got[0].tolist(), [each[0] for each in expected])
            for index, (_good, people, paid, received, holder, tile, given, taken) in enumerate(expected):
                people_slice, move_slice = slice(got[1][index], got[1][index + 1]), slice(got[5][index], got[5][index + 1])
                self.assertEqual((got[2][people_slice].tolist(), got[3][people_slice].tolist(), got[4][people_slice].tolist()),
                                 (people.tolist(), paid.tolist(), received.tolist()), seed)
                self.assertEqual((got[6][move_slice].tolist(), got[7][move_slice].tolist(), got[8][move_slice].tolist(), got[9][move_slice].tolist()),
                                 (holder, tile, given, taken), seed)


class WriteBatchWritesTheTables(unittest.TestCase):

    def test_random_batches(self):
        for seed in SEEDS:
            generator = numpy.random.default_rng(seed)
            bids, offers = plain.random_tables(generator, 25, 25)
            markets = int(generator.integers(1, 5))
            bid_ptr = numpy.concatenate(([0], numpy.cumsum(generator.integers(0, 4, markets)))).astype(numpy.int64)
            offer_ptr = numpy.concatenate(([0], numpy.cumsum(generator.integers(0, 4, markets)))).astype(numpy.int64)
            bid_rows = generator.permutation(25)[:bid_ptr[-1]].astype(numpy.int64)
            offer_rows = generator.permutation(25)[:offer_ptr[-1]].astype(numpy.int64)
            pair_ptr = numpy.concatenate(([0], numpy.cumsum(generator.integers(0, 3, markets)))).astype(numpy.int64)
            pairs_total = int(pair_ptr[-1])
            pair_bid = generator.integers(0, max(1, len(bid_rows)), pairs_total).astype(numpy.int64)
            pair_offer = generator.integers(0, max(1, len(offer_rows)), pairs_total).astype(numpy.int64)
            if not len(bid_rows) or not len(offer_rows):
                pair_ptr, pairs_total, pair_bid, pair_offer = numpy.zeros(markets + 1, dtype=numpy.int64), 0, pair_bid[:0], pair_offer[:0]
            tables = [BID_ORDER.new_table(BidOrder, 4), OFFER_ORDER.new_table(OfferOrder, 4), GOODS_PAIRS.new_table(GoodsPairs, 4),
                      GOODS_MARKET_RESULTS.new_table(GoodsMarketResults, 4)]
            for table in tables:
                table.row_count[0] = 2
            final = generator.random(len(offer_rows))
            allocated_offers = (generator.random(len(offer_rows)), generator.random(len(offer_rows)), generator.random(len(offer_rows)),
                                generator.integers(0, 5, len(offer_rows)).astype(numpy.int64))
            allocated_bids = (generator.random(len(bid_rows)), generator.random(len(bid_rows)))
            allocated_markets = (generator.integers(0, 2, markets) > 0, generator.random(markets), generator.random(markets),
                                 generator.random(markets), generator.random(markets))
            market_ids = generator.permutation(8)[:markets].astype(numpy.int64)
            pair_quantity = generator.random(pairs_total)
            arguments = (market_ids, bid_rows, bid_ptr, offer_rows, offer_ptr, final, allocated_offers, allocated_bids, allocated_markets,
                         pair_ptr, pair_bid, pair_offer, pair_quantity)
            expected_bids, expected_offers = copy_table(bids), copy_table(offers)
            expected = plain.plain_write_batch(expected_bids, expected_offers, *[copy_table(each) for each in tables], *arguments)
            got_bids, got_offers = copy_table(bids), copy_table(offers)
            grown = [reserve_rows(copy_table(table), extra) for table, extra in zip(
                tables, (len(bid_rows), len(offer_rows), pairs_total, markets))]
            goods_batch_write_kernel.write_batch(got_bids, got_offers, *grown, *arguments)
            same(self, got_bids, expected_bids)
            same(self, got_offers, expected_offers)
            for found, wanted in zip(grown, expected):
                self.assertEqual(int(found.row_count[0]), int(wanted.row_count[0]))
                for column, (kept, made) in enumerate(zip(found, wanted)):
                    if len(kept) > 1:
                        used = int(found.row_count[0])
                        self.assertTrue(numpy.array_equal(kept[:used], made[:used], equal_nan=kept.dtype.kind == "f"), column)


if __name__ == "__main__":
    unittest.main()
