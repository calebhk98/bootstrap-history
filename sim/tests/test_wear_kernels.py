"""The year's losses as rows (sim/economy/wear_kernels.py) against `inventory.spoilage_moves` and `wear_moves`, the Python they replace."""
QUICK_TOPIC = True

import unittest

import numpy as np

from sim.economy import inventory
from sim.economy.types import GoodSpec
from sim.economy.wear_kernels import loss_moves
from sim.tests.book_table_fixtures import StockBook, agents_table

AGENTS = ("zed", "amy", "edge:mint", "bob")           # agent numbers 0..3; sorted by name: amy, bob, edge:mint, zed
GOODS = ("wheat", "apple", "salt")                    # good numbers 0..2
TILES = ("t9", "t1", "t5")                            # tile numbers 0..2
HOLDINGS = [("zed", "wheat", "t9", 10.0), ("zed", "apple", "t1", 4.0), ("zed", "apple", "t9", 6.0), ("amy", "salt", "t5", 3.0),
            ("amy", "wheat", "t1", 0.0), ("bob", "wheat", "t1", 8.0), ("bob", "apple", "t5", -2.0), ("zed", "salt", "t1", 5.0)]
SPECS = {"wheat": GoodSpec("wheat", 1.0, 0.25, 0.0, "food"), "apple": GoodSpec("apple", 1.0, 1.5, 4.0, "food"),
         "salt": GoodSpec("salt", 1.0, 0.0, 0.5, "food")}


def ranks(names):
    ordered = sorted(range(len(names)), key=names.__getitem__)
    result = np.empty(len(names), dtype=np.int64)
    result[ordered] = np.arange(len(names))
    return result


def stock_book():
    book = StockBook(agents_table(0, 0, 1, 0), goods=3)
    book.stocks.reserve(32)
    for agent, good, tile, quantity in HOLDINGS:
        book.hold(AGENTS.index(agent), GOODS.index(good), TILES.index(tile), quantity)
    return book


def rows_of(book, shares, takes_part):
    order = np.array(sorted(range(len(AGENTS)), key=AGENTS.__getitem__), dtype=np.int64)
    order = order[book.agents.is_edge[order] == 0]
    agents, slots, lost = loss_moves(order, book.agents.first_slot, book.stocks.table, np.array(shares), np.array(takes_part, dtype=np.uint8),
                                     ranks(list(GOODS)), ranks(list(TILES)))
    stocks = book.stocks.table
    return [(AGENTS[agent], GOODS[stocks.good[slot]], TILES[stocks.tile[slot]], quantity)
            for agent, slot, quantity in zip(agents.tolist(), slots.tolist(), lost.tolist())]


def holdings_of():
    return {(agent, good, tile): quantity for agent, good, tile, quantity in HOLDINGS if quantity > 0.0}


class LossMovesTests(unittest.TestCase):
    def test_spoilage_is_each_positive_stock_times_its_goods_share_in_agent_good_tile_name_order(self):
        old = [(move.giver, move.good, move.tile, move.quantity) for move in inventory.spoilage_moves(holdings_of(), SPECS)]
        shares = [0.25, 1.0, 0.0]               # wheat, apple (1.5 is held to one), salt
        self.assertEqual(rows_of(stock_book(), shares, [1, 1, 1, 1]), old)
        self.assertTrue(old)

    def test_wear_takes_only_the_agents_that_use_their_durables(self):
        old = [(move.giver, move.good, move.tile, move.quantity)
               for move in inventory.wear_moves(holdings_of(), SPECS, users={"zed", "bob"})]
        shares = [0.0, 0.25, 1.0]               # apple wears a quarter a year, salt's half-year life is held to one
        self.assertEqual(rows_of(stock_book(), shares, [1, 0, 0, 1]), old)
        self.assertEqual({row[0] for row in old}, {"zed"})

    def test_an_edge_account_and_a_stock_at_zero_or_below_lose_nothing(self):
        book = stock_book()
        book.hold(2, 0, 0, 50.0)         # the edge account holds wheat
        rows = rows_of(book, [1.0, 1.0, 1.0], [1, 1, 1, 1])
        self.assertNotIn("edge:mint", {row[0] for row in rows})
        self.assertNotIn(("amy", "wheat", "t1"), {row[:3] for row in rows})
        self.assertNotIn(("bob", "apple", "t5"), {row[:3] for row in rows})

    def test_a_loss_that_leaves_only_residue_takes_the_whole_holding(self):
        book = StockBook(agents_table(0), goods=1)
        book.stocks.reserve(8)
        book.hold(0, 0, 0, 1e-17)
        book.hold(0, 0, 1, 100.0)
        rows = rows_of_one(book, [0.25])
        self.assertEqual(sorted(row[3] for row in rows), [1e-17 * 1.0, 25.0])

    def test_a_loss_that_leaves_a_real_remainder_takes_only_the_share(self):
        book = StockBook(agents_table(0), goods=1)
        book.stocks.reserve(8)
        book.hold(0, 0, 0, 1e-3)
        self.assertEqual([row[3] for row in rows_of_one(book, [0.25])], [0.25e-3])


def rows_of_one(book, shares):
    agents, slots, lost = loss_moves(np.array([0], dtype=np.int64), book.agents.first_slot, book.stocks.table, np.array(shares),
                                     np.array([1], dtype=np.uint8), np.array([0]), np.array([0, 1]))
    return [(agent, slot, 0, quantity) for agent, slot, quantity in zip(agents.tolist(), slots.tolist(), lost.tolist())]


if __name__ == "__main__":
    unittest.main()
