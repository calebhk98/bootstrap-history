"""Stage 4, plans and the rare order sources: each piece called on its own, with the inputs written out.

`stock_block` reads many stock cells in one call; `plan_sums` adds a producer's bids as Python's `sum` does; `OrderRows` into a
a `GoodsOrderBook` given named items gives the rows and the ids a book holding the same orders as objects gives; `plan_table.write_bids` does the same for the
plans of random economies (the producers' plans as `Plan` objects are the reference)."""

QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.book import Book
from sim.book_types import GoodsMove
from sim.economy import plan_table, plan_year
from sim.economy.goods_order_book import GoodsOrderBook
from sim.economy.goods_order_tables import MINT, STATE
from sim.economy.market_tables import MarketTables
from sim.economy.order_rows import OrderRows
from sim.economy.plan_table import plan_sums
from sim.economy.stock_block import numbers_of, stock_block
from sim.economy.types import EDGE_PRODUCTION, Bid, Offer
from sim.economy.year_arrays import YearArrays
from sim.economy.year_arrays_costs import refreshed
from sim.tests.year_close_fixture import MONEY, economy_of


class StockBlockTests(unittest.TestCase):

    def test_cells_read_their_stock_and_unknown_cells_read_zero(self):
        book = Book()
        book.post((), [GoodsMove(EDGE_PRODUCTION, "farm", "wheat", "T0", 5.0, "made"), GoodsMove(EDGE_PRODUCTION, "farm", "oats", "T1", 2.0, "made"),
                       GoodsMove(EDGE_PRODUCTION, "mill", "wheat", "T0", 7.5, "made")])
        agents = numbers_of(book.agent_ids, ["farm", "farm", "mill", "nobody", "mill"])
        goods = numbers_of(book.good_ids, ["wheat", "oats", "wheat", "wheat", "oats"])
        tiles = numbers_of(book.tile_ids, ["T0", "T1", "T0", "T0", "T1"])
        self.assertEqual(agents[3], -1)
        self.assertEqual(stock_block(book, agents, goods, tiles).tolist(), [5.0, 2.0, 7.5, 0.0, 0.0])
        self.assertEqual(stock_block(book, [], [], []).tolist(), [])


class PlanSumsTests(unittest.TestCase):

    def test_budgets_and_lines_add_as_python_sum_adds(self):
        rng = random.Random(4)
        wage_line = numpy.array([rng.uniform(-5.0, 1e6) for _each in range(6)])
        counts = [0, 3, 1, 12, 0, 40]
        budgets = [rng.uniform(-1.0, 1e6) * 10.0 ** rng.randint(-6, 6) for _each in range(sum(counts))]
        start = numpy.concatenate([[0], numpy.cumsum(counts)]).astype(numpy.int64)
        budget_total, outlay_total = plan_sums(wage_line, numpy.array(budgets), start)
        for producer in range(6):
            own = budgets[start[producer]:start[producer + 1]]
            self.assertEqual(budget_total[producer], sum(own))
            self.assertEqual(outlay_total[producer], sum(max(0.0, line) for line in [wage_line[producer].item()] + own))


def snapshot(book: GoodsOrderBook) -> dict:
    """What the order tables and the ids hold, to compare two books."""
    bids, offers = book.tables()
    count_bids, count_offers = int(bids.row_count[0]), int(offers.row_count[0])
    return {
        "bids": {name: getattr(bids, name)[:count_bids].tolist() for name in ("buyer", "good", "tile", "market", "sequence", "priority", "floor_quantity",
                                                                          "flexible_quantity", "reference_price", "elasticity", "budget", "maximum_price")},
        "offers": {name: getattr(offers, name)[:count_offers].tolist() for name in ("seller", "good", "tile", "market", "sequence", "quantity", "reservation_price")},
        "agents": list(book.book.agent_ids.name_list), "goods": list(book.book.good_ids.name_list), "tiles": list(book.book.tile_ids.name_list),
        "markets": list(book.memory_tables.goods_markets.name_list)}


class OrderRowsTests(unittest.TestCase):

    def test_named_rows_are_numbered_and_ordered_as_the_objects_they_replace(self):
        bids = [Bid("zed", "wheat", "north", "T1", 1.0, 2.0, 3.0, 0.5, 10.0), Bid("amy", "oats", "south", "T2", 0.0, 4.0, 2.0, 0.0, 8.0, 1, 9.0),
                Bid("mid", "barley", "north", "T0", 2.0, 0.0, 1.0, 0.0, 5.0)]
        offers = [Offer("kim", "salt", "south", "T2", 6.0, 1.5), Offer("abe", "wheat", "north", "T1", 3.0, 2.5)]
        objects = GoodsOrderBook(Book(), MarketTables())
        for bid in bids:
            objects.add_bid(bid)
        for offer in offers:
            objects.add_offer(offer)
        named = GoodsOrderBook(Book(), MarketTables())
        named.add_bid(bids[0])                                  # an object between named items keeps its place
        rows = OrderRows(named, STATE)
        rows.bids_from(bids[1:2])
        rows.offers_from(offers[:1])
        rows.write()
        mint = OrderRows(named, MINT)
        mint.bid(*(getattr(bids[2], field) for field in ("buyer", "good", "area", "tile", "floor_quantity", "flexible_quantity",
                                                         "reference_price", "elasticity", "budget", "priority", "maximum_price")))
        mint.offer("abe", "wheat", "north", "T1", 3.0, 2.5)
        mint.write()
        self.assertEqual(snapshot(named), snapshot(objects))

    def test_a_plain_book_and_a_dict_get_the_same_orders(self):
        rows_book = GoodsOrderBook(Book(), MarketTables())
        rows = OrderRows(rows_book, STATE)
        rows.bid("amy", "oats", "south", "T2", 0.0, 4.0, 2.0, 0.0, 8.0)
        rows.offer("kim", "salt", "south", "T2", 6.0, 1.5)
        rows.write()
        as_dict = {}
        again = OrderRows(as_dict, STATE)
        again.bid("amy", "oats", "south", "T2", 0.0, 4.0, 2.0, 0.0, 8.0)
        again.offer("kim", "salt", "south", "T2", 6.0, 1.5)
        again.write()
        self.assertEqual(rows_book.bids_of([0]), as_dict[("oats", "south")][0])
        self.assertEqual(rows_book.offers_of([0]), as_dict[("salt", "south")][1])


class PlanBidsTests(unittest.TestCase):

    def test_the_plan_tables_rows_are_the_bids_of_the_plans(self):
        compared = 0
        for seed in range(4):
            setup, record, view, _ledger, area_map = economy_of(seed, producer_count=60)
            arrays = refreshed(YearArrays.build(setup, record, area_map, view), setup, record, view)
            table = plan_year.plans_of(setup, record, view, arrays, MONEY)
            objects = GoodsOrderBook(Book(), MarketTables())
            for producer_id in table.ids:
                for bid in table.plan_of(producer_id).bids:
                    objects.add_bid(bid)
            named = GoodsOrderBook(Book(), MarketTables())
            plan_table.write_bids(table, named)
            self.assertEqual(snapshot(named), snapshot(objects))
            compared += objects.bid_count()
            budgets = table.budget_total_by_id()
            for producer_id in table.ids:
                self.assertEqual(budgets[producer_id], sum(bid.budget for bid in table.plan_of(producer_id).bids))
        self.assertGreater(compared, 50)


if __name__ == "__main__":
    unittest.main()
