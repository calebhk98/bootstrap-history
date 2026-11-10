"""Whole-table reads of the book (sim/book_read_kernels.py): many balances, many stocks, one agent's holdings, totals."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.book_read_kernels import (counted_stocks, currency_values, find_slots, good_quantities,
                                   read_balances, read_stocks_at)
from sim.book_holdings_kernels import many_holder_columns
from sim.tests.book_table_fixtures import STRIDE, StockBook, agents_table, balances_table


def held_book():
    book = StockBook(agents_table(0, 0, 1))
    for agent, good, tile, quantity in ((0, 0, 1, 5.0), (1, 0, 1, 2.0), (0, 1, 2, 7.0), (2, 0, 1, 100.0), (0, 0, 3, 0.0)):
        book.hold(agent, good, tile, quantity)
    return book


class BalanceReadTests(unittest.TestCase):
    def test_each_agents_balance_is_read_and_an_unknown_agent_or_currency_reads_zero(self):
        balances = balances_table(3, {0: 1.0, STRIDE + 1: 2.0, 2 * STRIDE: 3.0})
        self.assertEqual(read_balances(balances, STRIDE, numpy.array([0, 1, -1, 2]), 1).tolist(), [0.0, 2.0, 0.0, 0.0])
        self.assertEqual(read_balances(balances, STRIDE, numpy.array([0, 2]), -1).tolist(), [0.0, 0.0])


class StockReadTests(unittest.TestCase):
    def test_slots_are_found_by_agent_and_tile_and_minus_one_when_never_held(self):
        book = held_book()
        slots = find_slots(book.stocks.table, book.stocks.index, numpy.array([0, 1, 0, -1]), 0, numpy.array([1, 1, 2, 1]))
        self.assertEqual(slots.tolist(), [0, 1, -1, -1])

    def test_an_unknown_good_finds_no_slots(self):
        book = held_book()
        self.assertEqual(find_slots(book.stocks.table, book.stocks.index, numpy.array([0]), -1, numpy.array([1])).tolist(), [-1])

    def test_quantities_are_read_by_slot_and_a_missing_slot_reads_zero(self):
        book = held_book()
        self.assertEqual(read_stocks_at(book.stocks.table, numpy.array([0, -1, 2])).tolist(), [5.0, 0.0, 7.0])


class HolderTests(unittest.TestCase):
    def test_the_columns_of_agents_slots_come_in_the_order_given_and_the_order_the_slots_were_made(self):
        book = held_book()
        table = book.stocks.table
        starts, owner, goods, tiles, quantities = many_holder_columns(
            book.agents.first_slot[:3][[1, 0]], table.next_in_agent, table.good, table.tile, table.quantity)
        self.assertEqual((starts.tolist(), owner.tolist(), goods.tolist(), tiles.tolist(), quantities.tolist()),
                         ([0, 1, 4], [0, 1, 1, 1], [0, 0, 1, 0], [1, 1, 2, 3], [2.0, 5.0, 7.0, 0.0]))

    def test_an_agent_with_no_slots_has_none(self):
        book = StockBook(agents_table(0))
        starts, owner, goods, _tiles, _quantities = many_holder_columns(
            book.agents.first_slot[:1], book.stocks.table.next_in_agent, book.stocks.table.good, book.stocks.table.tile,
            book.stocks.table.quantity)
        self.assertEqual((starts.tolist(), owner.tolist(), goods.tolist()), ([0, 0], [], []))


class TotalsTests(unittest.TestCase):
    def test_counted_stocks_leave_out_edge_accounts_and_empty_slots(self):
        book = held_book()
        goods, quantities = counted_stocks(book.stocks.table, book.agents)
        self.assertEqual((goods.tolist(), quantities.tolist()), ([0, 0, 1], [5.0, 2.0, 7.0]))

    def test_a_slot_given_up_by_a_rename_is_not_counted(self):
        book = held_book()
        book.stocks.table.live[0] = 0
        self.assertEqual(counted_stocks(book.stocks.table, book.agents)[1].tolist(), [2.0, 7.0])

    def test_currency_values_skip_edge_accounts_unless_asked(self):
        balances = balances_table(3, {0: 1.0, STRIDE: 2.0, 2 * STRIDE: 30.0})
        agents = agents_table(0, 0, 1)
        self.assertEqual((currency_values(balances, STRIDE, 0, agents, False).tolist(),
                          currency_values(balances, STRIDE, 0, agents, True).tolist()), ([1.0, 2.0], [1.0, 2.0, 30.0]))

    def test_good_quantities_list_every_live_slot_of_the_good_in_slot_order(self):
        self.assertEqual(good_quantities(held_book().stocks.table, 0).tolist(), [5.0, 2.0, 100.0, 0.0])


if __name__ == "__main__":
    unittest.main()
