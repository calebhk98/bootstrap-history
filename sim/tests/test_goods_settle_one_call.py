"""`goods_settle.settle_good` (one kernel call per good: `goods_settle_kernel.settle_good_markets`) against the steps it replaced
(`goods_settle_plain.plain_settle_good`: `settle_by_ids`, then the ledger's notes by several calls) on the same random batches: the same
goods moved, buyers and mint takes, and afterwards the same rows in every table of the book and of the ledger. Random pairs on random purses
and stocks, with and without customs accounts, with markets that did not trade left out, and from books that need room or a purpose number
on the first call. Also a written-out case, and a good with a market that did not trade in the batch (left to the object path). Under numba
and ROME_NO_JIT=1."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

import numpy

from sim.book import Book
from sim.book_types import MINT_ID
from sim.economy.goods_good_clear import ON_OBJECTS, TABLE_TRADED, TABLE_UNTRADED
from sim.economy.goods_order_book import GoodsOrderBook
from sim.economy.goods_settle import settle_good
from sim.economy.goods_settle_one_call import settle_in_one_call
from sim.economy.goods_table_views import TableBatch
from sim.economy.market_tables import MarketTables
from sim.economy.types import EDGE_MINT, Bid, GoodsMove, Offer, Transfer
from sim.economy.year_ledger import YearLedger
from sim.tests.goods_settle_plain import plain_settle_good
from sim.tests.test_goods_settle_ids import BUYERS, GOOD, MONEY, SELLERS, TILES, scenario


class Cleared:
    """The columns of a `GoodClearing` that settlement reads."""

    def __init__(self, batch, orders, quantity, way):
        self.batch, self.quantity, self.way, self.slots = batch, numpy.array(quantity), numpy.array(way, dtype=numpy.int64), numpy.arange(3)
        self.context = SimpleNamespace(setup=SimpleNamespace(currency_id=MONEY))
        self.bought = None

    def __len__(self):
        return len(self.quantity)


def table_rows(table):
    """Every column of a table cut to the rows it holds (the whole column where the table has no row count)."""
    rows = int(table.row_count[0]) if "row_count" in table._fields else None
    return {name: (column if rows is None or name in ("row_count", "capacity") else column[:rows]).tolist()
            for name, column in zip(table._fields, table) if name != "capacity"}


def state(book, ledger):
    """The rows of the book's and the ledger's tables."""
    tables = ledger.tables
    book_tables = book.tables()
    return ({"money": [table_rows(book_tables.money.agents), table_rows(book_tables.money.balances), table_rows(book_tables.money.currencies)],
             "goods": [table_rows(table) for table in (book_tables.goods.goods, book_tables.goods.stocks, book_tables.goods.flows,
                                                       book_tables.goods.edge_goods)]},
            table_rows(tables.figures), tables.counters.tolist(), {name: table_rows(store.rows.table) for name, store in tables.pairs.items()})


def setup(seed):
    """(record, ledger, cleared, plant makers) of a random batch of three markets, a market of which may not have traded."""
    rng = random.Random(seed)
    orders, batch, _results = scenario(seed)
    border = seed % 2 == 0
    ledger = YearLedger(frozenset(["s2"]) if border else frozenset(), frozenset(["b2"]) if border else frozenset(), book=orders.book,
                        markets=orders.memory_tables)
    quantity = [rng.choice([0.0, 1.0, 2.0]) for _ in range(3)]
    return SimpleNamespace(book=orders.book), ledger, Cleared(batch, orders, quantity, [TABLE_TRADED] * 3), {GOOD: ["b2", "s1"]}


def one_pair(buyer, imports=frozenset(), exports=frozenset()):
    """(record, ledger, cleared) of one market: `buyer` takes 3 units from s1 at the ask of 2; the buyer has 10 coins, s1 has 5 units."""
    orders = GoodsOrderBook(Book(), MarketTables())
    book = orders.book
    orders.add_bid(Bid(buyer, GOOD, "north", "t1", 1.0, 1.0, 2.0, 0.5, 50.0, 0))
    orders.add_offer(Offer("s1", GOOD, "north", "t1", 5.0, 1.0))
    book.post([Transfer(EDGE_MINT, buyer, MONEY, 10.0, "start")] if buyer != MINT_ID else [],
              [GoodsMove(EDGE_MINT, "s1", GOOD, "t1", 5.0, "start")])
    arrays = (numpy.ones(1, dtype=numpy.uint8), numpy.ones(1), numpy.ones(1), numpy.ones(1), numpy.ones(1), numpy.array([2.0]),
              numpy.zeros(1), numpy.zeros(1), numpy.arange(1), numpy.zeros(1), numpy.zeros(1), numpy.array([0, 1]), numpy.array([0]),
              numpy.array([0]), numpy.array([3.0]))
    pack = SimpleNamespace(bid_rows=numpy.array([0]), offer_rows=numpy.array([0]), bid_ptr=numpy.array([0, 1]), offer_ptr=numpy.array([0, 1]))
    cleared = Cleared(TableBatch(arrays, pack, orders), orders, [3.0], [TABLE_TRADED])
    cleared.slots = numpy.arange(1)
    return SimpleNamespace(book=book), YearLedger(imports, exports, book=book, markets=orders.memory_tables), cleared


def answer_figures(answer, cleared, count):
    """What a caller reads from a `GoodSettlement`: goods moved, the buyers of each market, the mint's takes, and `cleared.bought`."""
    return (answer.delivered.tolist(), [answer.bought(place).columns() if hasattr(answer.bought(place), "columns") else answer.bought(place)
                                        for place in range(count)],
            {place: answer.takes[place] for place in answer.takes}, None if cleared.bought is None else [each.tolist() for each in cleared.bought])


def same(testcase, found, expected, message):
    """Assert two nested figures are equal, comparing arrays by value."""
    if isinstance(expected, (tuple, list)) and isinstance(found, (tuple, list)):
        testcase.assertEqual(len(found), len(expected), message)
        for each, other in zip(found, expected):
            same(testcase, each, other, message)
    elif isinstance(expected, numpy.ndarray):
        testcase.assertTrue(numpy.array_equal(found, expected), message)
    else:
        testcase.assertEqual(found, expected, message)


class SettleGoodInOneCall(unittest.TestCase):

    def test_random_batches_settle_as_the_steps_it_replaced_settle_them(self):
        for seed in range(80):
            fused_record, fused_ledger, fused_cleared, makers = setup(seed)
            plain_record, plain_ledger, plain_cleared, _makers = setup(seed)
            found = settle_good(fused_record, fused_ledger, fused_cleared, GOOD, makers)
            expected = plain_settle_good(plain_record, plain_ledger, plain_cleared, GOOD, makers)
            same(self, answer_figures(found, fused_cleared, 3), answer_figures(expected, plain_cleared, 3), seed)
            self.assertEqual(state(fused_record.book, fused_ledger), state(plain_record.book, plain_ledger), seed)

    def test_a_good_with_a_market_off_the_batch_is_left_to_the_object_path(self):
        record, ledger, cleared, makers = setup(1)
        cleared.quantity[:] = 1.0
        cleared.way[1] = ON_OBJECTS
        ledger.tables.fit_agents()
        before = state(record.book, ledger)
        self.assertIsNone(settle_in_one_call(record, ledger, cleared, GOOD, makers))
        self.assertEqual(state(record.book, ledger), before)

    def test_markets_that_did_not_trade_settle_nothing(self):
        record, ledger, cleared, makers = setup(1)
        cleared.quantity[:] = 0.0
        cleared.way[:] = TABLE_UNTRADED
        before = state(record.book, ledger)
        answer = settle_good(record, ledger, cleared, GOOD, makers)
        self.assertEqual(answer.delivered.tolist(), [0.0, 0.0, 0.0])
        self.assertEqual(state(record.book, ledger), before)
        self.assertIsNone(cleared.bought)

    def test_three_units_bought_at_two_move_six_coins_and_three_units(self):
        record, ledger, cleared = one_pair("b1")
        book = record.book
        answer = settle_good(record, ledger, cleared, GOOD, {})
        self.assertEqual(answer.delivered.tolist(), [3.0])
        self.assertEqual((book.balance("b1", MONEY), book.balance("s1", MONEY)), (4.0, 6.0))
        self.assertEqual((book.stock("b1", GOOD, "t1"), book.stock("s1", GOOD, "t1")), (3.0, 2.0))
        self.assertEqual((ledger.money_out["b1"], ledger.sales_in["s1"]), (6.0, 6.0))
        self.assertEqual((ledger.received["b1"][GOOD], ledger.sold["s1", GOOD]), (3.0, 3.0))
        self.assertEqual([each.tolist() for each in cleared.bought], [[0], [book.agent_ids.numbers["b1"]], [3.0], [6.0]])

    def test_goods_sold_to_the_mint_are_its_takes_and_the_book_is_as_the_steps_left_it(self):
        fused_record, fused_ledger, fused_cleared = one_pair(MINT_ID)
        plain_record, plain_ledger, plain_cleared = one_pair(MINT_ID)
        found = settle_good(fused_record, fused_ledger, fused_cleared, GOOD, {})
        expected = plain_settle_good(plain_record, plain_ledger, plain_cleared, GOOD, {})
        self.assertEqual(found.takes, {0: {("s1", "t1"): 3.0}})
        same(self, answer_figures(found, fused_cleared, 1), answer_figures(expected, plain_cleared, 1), "mint")
        self.assertEqual(state(fused_record.book, fused_ledger), state(plain_record.book, plain_ledger))

    def test_money_across_the_border_is_noted_in_the_ledger_as_the_steps_noted_it(self):
        fused_record, fused_ledger, fused_cleared = one_pair("b1", frozenset(["s1"]), frozenset(["b1"]))
        plain_record, plain_ledger, plain_cleared = one_pair("b1", frozenset(["s1"]), frozenset(["b1"]))
        settle_good(fused_record, fused_ledger, fused_cleared, GOOD, {})
        plain_settle_good(plain_record, plain_ledger, plain_cleared, GOOD, {})
        self.assertTrue(len(fused_ledger.imports_paid) + len(fused_ledger.exports_received) > 0)
        self.assertEqual(state(fused_record.book, fused_ledger), state(plain_record.book, plain_ledger))


if __name__ == "__main__":
    unittest.main()
