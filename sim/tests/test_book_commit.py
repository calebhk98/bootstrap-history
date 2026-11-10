"""Writing a planned batch and its records (sim/book_commit.py): balances, stock slots and their chains, gross totals, flows."""
QUICK_TOPIC = True

import unittest

from sim.book_commit import (add_flow, commit_money, commit_stock, create_slot, record_edge_goods, record_edge_money,
                             record_moves, record_transfers)
from sim.book_index import pack_key
from sim.book_plan import plan_transfers
from sim.book_tables import TABLE_FULL
from sim.compiled_tables.causes import OK
from sim.compiled_tables.growth import NO_ROOM
from sim.tests.book_table_fixtures import (STRIDE, StockBook, agents_table, balances_table, money_tables, moves_of,
                                           plan_and_index, transfers_of)


class CommitMoneyTests(unittest.TestCase):
    def test_every_planned_balance_is_written_seen_and_its_agent_known(self):
        balances, agents = balances_table(2, {0: 10.0}), agents_table(0, 0)
        plan, local = plan_and_index(8)
        plan_transfers(transfers_of((0, 1, 0, 4.0)), 0, 1, balances, STRIDE, plan, local)
        commit_money(plan, balances, agents)
        self.assertEqual((balances.amount[0], balances.amount[STRIDE], balances.seen[STRIDE], agents.known.tolist()),
                         (6.0, 4.0, 1, [1, 1]))


class CreateSlotTests(unittest.TestCase):
    def test_slots_of_one_agent_are_chained_in_the_order_they_were_made(self):
        agents = agents_table(0, 0)
        book = StockBook(agents)
        first, other, second = book.hold(0, 0, 1, 1.0), book.hold(1, 0, 1, 2.0), book.hold(0, 1, 2, 3.0)
        self.assertEqual((first, other, second), (0, 1, 2))
        self.assertEqual((agents.first_slot.tolist(), agents.last_slot.tolist(), book.stocks.table.next_in_agent[:3].tolist()),
                         ([0, 1], [2, 1], [2, -1, -1]))

    def test_the_slot_is_found_by_its_key_and_starts_at_zero(self):
        book = StockBook(agents_table(0))
        slot = create_slot(book.stocks.table, book.stocks.index, book.agents, pack_key(0, 1, 7))
        self.assertEqual((book.stocks.find(pack_key(0, 1, 7)), book.stocks.table.quantity[slot]), (slot, 0.0))

    def test_a_full_table_answers_no_room_and_makes_nothing(self):
        book = StockBook(agents_table(0))
        book.stocks.table.row_count[0] = int(book.stocks.table.capacity[0])
        self.assertEqual(create_slot(book.stocks.table, book.stocks.index, book.agents, pack_key(0, 0, 0)), NO_ROOM)


class CommitStockTests(unittest.TestCase):
    def test_a_planned_cell_without_a_slot_gets_one_and_the_agent_is_known(self):
        from sim.book_plan import plan_moves
        book = StockBook(agents_table(0, 0))
        book.hold(0, 0, 5, 10.0)
        plan, local = plan_and_index(8)
        plan_moves(moves_of((0, 1, 0, 5, 6, 4.0)), 0, 1, book.stocks.table, book.stocks.index, plan, local)
        self.assertEqual(commit_stock(plan, book.stocks.table, book.stocks.index, book.agents), OK)
        self.assertEqual((book.quantity(0, 0, 5), book.quantity(1, 0, 6), book.agents.known.tolist()), (6.0, 4.0, [1, 1]))

    def test_running_out_of_room_answers_table_full(self):
        from sim.book_plan import plan_moves
        book = StockBook(agents_table(0, 0))
        plan, local = plan_and_index(8)
        plan_moves(moves_of((0, 1, 0, 5, 6, 0.0)), 0, 1, book.stocks.table, book.stocks.index, plan, local)
        book.stocks.table.row_count[0] = int(book.stocks.table.capacity[0])
        self.assertEqual(commit_stock(plan, book.stocks.table, book.stocks.index, book.agents), TABLE_FULL)


class EdgeRecordTests(unittest.TestCase):
    def test_the_first_record_sets_volume_and_net_and_later_ones_add(self):
        balances = balances_table(1)
        record_edge_money(balances, 0, 5.0, -5.0)
        record_edge_money(balances, 0, 2.0, 2.0)
        self.assertEqual((balances.edge_volume[0], balances.edge_net[0], balances.edge_seen[0]), (7.0, -3.0, 1))

    def test_a_first_net_of_negative_zero_stays_negative_zero(self):
        balances = balances_table(1)
        record_edge_money(balances, 0, 0.0, -0.0)
        self.assertEqual(str(float(balances.edge_net[0])), "-0.0")

    def test_edge_goods_rows_are_made_at_first_sight_and_added_to_after(self):
        book = StockBook(agents_table(1))
        record_edge_goods(book.edge_goods.table, book.edge_goods.index, 0, 1, 3.0, 3.0)
        record_edge_goods(book.edge_goods.table, book.edge_goods.index, 0, 1, 2.0, -2.0)
        row = book.edge_goods.find(pack_key(0, 1))
        self.assertEqual((book.edge_goods.rows, book.edge_goods.table.volume[row], book.edge_goods.table.net[row]), (1, 5.0, 1.0))


class FlowTests(unittest.TestCase):
    def test_a_purpose_flow_starts_at_the_first_quantity_and_adds_in_order(self):
        book = StockBook(agents_table(0))
        add_flow(book.flows.table, book.flows.index, 1, 2, 3, 0.1)
        add_flow(book.flows.table, book.flows.index, 1, 2, 3, 0.2)
        add_flow(book.flows.table, book.flows.index, 1, 2, 4, 5.0)
        self.assertEqual((book.flows.rows, book.flows.table.quantity[:2].tolist()), (2, [0.1 + 0.2, 5.0]))


class RecordTests(unittest.TestCase):
    def test_transfers_add_to_the_gross_total_and_record_edge_payers_and_payees(self):
        agents, balances = agents_table(1, 0), balances_table(2)
        money = money_tables(agents, balances)
        record_transfers(transfers_of((0, 1, 1, 4.0), (1, 0, 1, 1.0)), 0, 2, money)
        self.assertEqual((money.currencies.gross_posted[1], money.currencies.gross_seen.tolist(),
                          balances.edge_volume[1], balances.edge_net[1]), (5.0, [0, 1], 5.0, 3.0))

    def test_moves_record_the_gross_total_the_purpose_flow_and_the_edge_goods(self):
        book = StockBook(agents_table(1, 0))
        record_moves(moves_of((0, 1, 1, 0, 0, 2.0), (0, 1, 1, 0, 0, 3.0)), 0, 2, book.tables())
        row = book.edge_goods.find(pack_key(0, 1))
        self.assertEqual((book.goods.gross_moved[1], book.flows.table.quantity[0], book.edge_goods.table.net[row]), (5.0, 5.0, 5.0))


if __name__ == "__main__":
    unittest.main()
