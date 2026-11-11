"""`goods_round_notes_kernel` against the numpy chains and ledger calls it replaced: the markets whose fills the ledger keeps
(`goods_round_notes_plain.plain_places_with_fills`) on seeded random clearings in each mode, and the rounds noted in the ledger's tables
(`year_ledger_arrays.note_round_rows`). Under numba and ROME_NO_JIT=1."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.economy import year_ledger_arrays
from sim.economy.goods_round_notes_kernel import ALL_TRADED, NO_TRADED, WATCHED_TRADED, markets_with_fills, note_good_rounds
from sim.economy.goods_good_clear import ON_OBJECTS, TABLE_TRADED, TABLE_UNTRADED
from sim.economy.year_ledger_store import LedgerTables
from sim.tests.goods_round_notes_plain import plain_places_with_fills

NO_FLAGS = numpy.zeros(0, dtype=numpy.bool_)
NO_NUMBERS = numpy.zeros(0, dtype=numpy.int64)


class MarketsWithFills(unittest.TestCase):

    def test_written_out_clearing_in_each_mode(self):
        way = numpy.array([TABLE_TRADED, TABLE_UNTRADED, ON_OBJECTS, TABLE_TRADED, TABLE_TRADED], dtype=numpy.int64)
        slots = numpy.array([0, -1, -1, 1, 2], dtype=numpy.int64)
        bid_ptr = numpy.array([0, 2, 3, 5], dtype=numpy.int64)
        watched = numpy.array([False, False, False, True, False])
        self.assertEqual(markets_with_fills(way, slots, bid_ptr, watched, ALL_TRADED).tolist(), [0, 2, 3, 4])
        self.assertEqual(markets_with_fills(way, slots, NO_NUMBERS, NO_FLAGS, NO_TRADED).tolist(), [2])
        self.assertEqual(markets_with_fills(way, slots, bid_ptr, watched, WATCHED_TRADED).tolist(), [2, 4])

    def test_random_clearings_keep_the_markets_the_numpy_chain_kept(self):
        generator = numpy.random.default_rng(5)
        for _ in range(200):
            count = int(generator.integers(0, 9))
            way = generator.integers(0, 3, count).astype(numpy.int64)
            batched = numpy.flatnonzero(way == TABLE_TRADED)
            slots = numpy.full(count, -1, dtype=numpy.int64)
            slots[batched] = generator.permutation(len(batched))
            bid_ptr = numpy.concatenate(([0], numpy.cumsum(generator.integers(0, 4, len(batched))))).astype(numpy.int64)
            watched = generator.integers(0, 2, bid_ptr[-1]).astype(numpy.bool_)
            for which, mask, watchers_set in ((ALL_TRADED, NO_FLAGS, False), (NO_TRADED, NO_FLAGS, True), (WATCHED_TRADED, watched, True)):
                found = markets_with_fills(way, slots, bid_ptr if which == WATCHED_TRADED else NO_NUMBERS, mask, which).tolist()
                self.assertEqual(found, plain_places_with_fills(way, slots, bid_ptr, None if which == NO_TRADED else watched, watchers_set))


class RoundsNoted(unittest.TestCase):

    def test_rounds_are_the_ledger_rows_note_round_rows_makes(self):
        generator = numpy.random.default_rng(9)
        for _ in range(30):
            found, expected = LedgerTables(), LedgerTables()
            count = int(generator.integers(1, 7))
            for tables in (found, expected):
                for area in range(count):
                    tables.market_number("grain", "area%d" % area)
            markets = generator.permutation(count).astype(numpy.int64)
            quantity = generator.integers(0, 3, count).astype(float)
            price = numpy.where(quantity > 0.0, generator.random(count) + 0.5, numpy.nan)
            moved = quantity * generator.integers(0, 2, count)
            year_ledger_arrays.note_round_rows(expected, markets, quantity, price, moved)
            found.fit_markets()
            found.reserve_rounds(count)
            way = numpy.full(count, TABLE_TRADED, dtype=numpy.int64)
            note_good_rounds(way, numpy.arange(count), NO_NUMBERS, NO_FLAGS, ALL_TRADED, found.rounds, found.market_figures.delivered,
                             found.market_figures.order_delivered, found.market_counters, markets, quantity, price, moved)
            for table, other in ((found.rounds, expected.rounds), (found.market_figures, expected.market_figures)):
                for name, column, wanted in zip(table._fields, table, other):
                    self.assertTrue(numpy.array_equal(column[:int(table.row_count[0])], wanted[:int(other.row_count[0])], equal_nan=True)
                                    if name not in ("capacity",) and column.ndim == 1 else True, name)
            self.assertEqual(found.market_counters.tolist(), expected.market_counters.tolist())


if __name__ == "__main__":
    unittest.main()
