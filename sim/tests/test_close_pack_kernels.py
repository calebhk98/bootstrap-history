"""The kernels that fill the close pack (sim/economy/close_pack_kernels.py) against the per-agent Python they replace, bit for bit."""
QUICK_TOPIC = True

import math
import unittest

import numpy

from sim.economy.close_pack_kernels import held_goods, pair_values_by_slot, slot_stocks
from sim.economy.year_ledger import YearLedger
from sim.tests.book_table_fixtures import StockBook, agents_table

# agent -> {(good, tile): quantity}; goods 0..3, tiles 0..2; good 3 has no column in the matrices
HOLDINGS = {
    0: {(0, 0): 5.0, (0, 1): 2.5, (1, 0): 7.0, (3, 0): 4.0},
    1: {(2, 1): -1.5, (2, 2): 0.0, (1, 1): 0.1, (1, 2): 0.2, (1, 0): 0.3},
    2: {(1, 0): 0.0},
    4: {(0, 2): 1e-17, (0, 0): 1e16, (0, 1): 1.0, (0, 3): -1e16},
}
COLUMN_OF_BOOK_GOOD = numpy.array([2, 0, 1, -1], dtype=numpy.int64)       # book good number -> matrix column


def book_holding():
    book = StockBook(agents_table(0, 0, 0, 0, 0))
    book.stocks.reserve(32)
    for agent, held in HOLDINGS.items():
        for (good, tile), quantity in held.items():
            book.hold(agent, good, tile, quantity)
    return book


def old_held(held):
    """The old pack's rule for one agent: goods in column order, listed when any tile is not zero, the exact sum of the positive tiles."""
    by_good = {}
    for (good, tile), quantity in held.items():
        by_good.setdefault(good, {})[tile] = quantity
    listed = []
    for good in sorted(by_good, key=lambda each: COLUMN_OF_BOOK_GOOD[each]):
        column = COLUMN_OF_BOOK_GOOD[good]
        tiles = by_good[good]
        if column >= 0 and any(value != 0.0 for value in tiles.values()):
            listed.append((int(column), math.fsum(value for value in tiles.values() if value > 0.0)))
    return listed


class HeldGoodsTests(unittest.TestCase):
    def test_each_producers_goods_are_listed_in_column_order_with_exact_sums_of_the_positive_tiles(self):
        book = book_holding()
        numbers = numpy.array([0, 1, 2, 3, 4, -1], dtype=numpy.int64)
        start, columns, quantities = held_goods(book.agents.first_slot, book.stocks.table, numbers, COLUMN_OF_BOOK_GOOD)
        for position, agent in enumerate(numbers.tolist()):
            wanted = old_held(HOLDINGS.get(agent, {}))
            first, last = start[position], start[position + 1]
            self.assertEqual(list(zip(columns[first:last].tolist(), quantities[first:last].tolist())), wanted)

    def test_the_sum_of_three_tiles_is_the_correctly_rounded_one_not_a_left_to_right_one(self):
        book = book_holding()
        _start, _columns, quantities = held_goods(book.agents.first_slot, book.stocks.table, numpy.array([4]), COLUMN_OF_BOOK_GOOD)
        self.assertEqual(quantities.tolist(), [math.fsum([1e-17, 1e16, 1.0])])
        self.assertNotEqual(quantities[0], 1e-17 + 1e16 + 1.0)


class SlotStocksTests(unittest.TestCase):
    def test_a_producer_reads_the_good_of_each_slot_on_its_own_tile_and_a_missing_holding_reads_zero(self):
        book = book_holding()
        slot_goods = numpy.array([[0, 1, -1], [2, -1, -1]], dtype=numpy.int64)       # recipe by slot: book good number
        found = slot_stocks(book.stocks.table, book.stocks.index, numpy.array([0, 0, 1, 1, -1, 3]),
                            numpy.array([0, 1, 1, 2, 0, 0]), numpy.array([0, 0, 1, 0, 0, 1]), slot_goods)
        self.assertEqual(found.tolist(), [[5.0, 7.0, 0.0], [2.5, 0.0, 0.0], [-1.5, 0.0, 0.0], [0.0, 0.2, 0.0],
                                          [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])


class PairValuesTests(unittest.TestCase):
    def test_a_pair_table_is_read_by_agent_and_the_subkey_of_each_slot(self):
        ledger = YearLedger()
        ledger.sold[("farm", "wheat")] = 3.5
        ledger.sold[("farm", "barley")] = 1.25
        ledger.sold[("mill", "wheat")] = 9.0
        tables = ledger.tables
        book = tables.book
        farm, mill, shop = (book.agent_ids.numbers.get(name, -1) for name in ("farm", "mill", "shop"))
        wheat, barley = book.good_ids.numbers["wheat"], book.good_ids.numbers["barley"]
        slot_keys = numpy.array([[wheat, barley, -1], [barley, -1, -1]], dtype=numpy.int64)
        store = tables.pairs["sold"]
        found = pair_values_by_slot(store.rows.table, store.rows.index, numpy.array([farm, mill, shop, -1]),
                                    numpy.array([0, 1, 0, 0]), slot_keys)
        self.assertEqual(found.tolist(), [[3.5, 1.25, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])


if __name__ == "__main__":
    unittest.main()
