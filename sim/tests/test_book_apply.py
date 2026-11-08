"""Applying postings (sim/book_apply.py): a batch is written whole or not at all, and each batch's outcome says which."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.book_apply import RULE_BATCH, RULE_SINGLE, apply_batches, apply_goods, apply_money, apply_settled
from sim.book_tables import (BATCH_OUTCOMES, BookTables, BatchOutcomes, INSUFFICIENT_FUNDS, INSUFFICIENT_GOODS,
                             NEGATIVE_AMOUNT, NEGATIVE_QUANTITY)
from sim.compiled_tables.causes import OK
from sim.tests.book_table_fixtures import (STRIDE, StockBook, agents_table, balances_table, money_tables, moves_of,
                                           plan_and_index, scratch_for, transfers_of)


def book_of(balances_by_cell, edges=(0, 0, 0)):
    agents = agents_table(*edges)
    stock = StockBook(agents)
    stock.hold(0, 0, 1, 10.0)
    return BookTables(money_tables(agents, balances_table(len(edges), balances_by_cell)), stock.tables()), stock


class ApplyMoneyTests(unittest.TestCase):
    def test_a_funded_batch_is_written_and_recorded(self):
        tables, _stock = book_of({0: 10.0})
        plan, local = plan_and_index(8)
        result = apply_money(transfers_of((0, 1, 0, 4.0)), 0, 1, tables.money, plan, local, RULE_BATCH)
        self.assertEqual((result, tables.money.balances.amount[0], tables.money.balances.amount[STRIDE],
                          tables.money.currencies.gross_posted[0]), ((OK, -1), 6.0, 4.0, 4.0))

    def test_an_overdraft_writes_nothing_and_names_the_cell(self):
        tables, _stock = book_of({0: 1.0})
        plan, local = plan_and_index(8)
        result = apply_money(transfers_of((0, 1, 0, 4.0)), 0, 1, tables.money, plan, local, RULE_BATCH)
        self.assertEqual((result, tables.money.balances.amount[0], tables.money.balances.seen[STRIDE]),
                         ((INSUFFICIENT_FUNDS, 0), 1.0, 0))

    def test_a_single_posting_is_held_to_the_balance_before_it(self):
        tables, _stock = book_of({0: 4.0})
        plan, local = plan_and_index(8)
        result = apply_money(transfers_of((0, 1, 0, 5.0)), 0, 1, tables.money, plan, local, RULE_SINGLE)
        self.assertEqual(result, (INSUFFICIENT_FUNDS, 0))


class ApplyGoodsTests(unittest.TestCase):
    def test_a_funded_batch_moves_the_stock_and_leaves_the_purpose_flow(self):
        tables, stock = book_of({})
        plan, local = plan_and_index(8)
        result = apply_goods(moves_of((0, 1, 0, 1, 2, 4.0)), 0, 1, tables.goods, plan, local, RULE_BATCH)
        self.assertEqual((result, stock.quantity(0, 0, 1), stock.quantity(1, 0, 2), stock.flows.table.quantity[0]),
                         ((OK, -1), 6.0, 4.0, 4.0))

    def test_an_overdraft_leaves_the_stock_alone(self):
        tables, stock = book_of({})
        plan, local = plan_and_index(8)
        result = apply_goods(moves_of((0, 1, 0, 1, 1, 40.0)), 0, 1, tables.goods, plan, local, RULE_BATCH)
        self.assertEqual((result[0], stock.quantity(0, 0, 1), stock.stocks.rows), (INSUFFICIENT_GOODS, 10.0, 1))


class ApplyBatchesTests(unittest.TestCase):
    def run_batches(self, tables, transfers, moves, transfer_starts, move_starts, stop):
        outcomes = BATCH_OUTCOMES.new_table(BatchOutcomes, len(transfer_starts) - 1)
        scratch = scratch_for(4, 4)
        refused = apply_batches(transfers, numpy.array(transfer_starts), moves, numpy.array(move_starts), len(transfer_starts) - 1,
                                tables, scratch, outcomes, RULE_BATCH, stop)
        return refused, outcomes

    def test_a_refused_batch_does_not_stop_the_next_one_and_each_has_an_outcome(self):
        tables, _stock = book_of({0: 5.0})
        transfers = transfers_of((0, 1, 0, 4.0), (0, 1, 0, 40.0), (0, 2, 0, 1.0))
        moves = moves_of()
        refused, outcomes = self.run_batches(tables, transfers, moves, [0, 1, 2, 3], [0, 0, 0, 0], False)
        self.assertEqual((refused, outcomes.code.tolist(), outcomes.culprit.tolist(), int(outcomes.row_count[0])),
                         (1, [OK, INSUFFICIENT_FUNDS, OK], [-1, 0, -1], 3))
        self.assertEqual(tables.money.balances.amount[0], 0.0)

    def test_stop_on_refusal_leaves_the_later_batches_unapplied(self):
        tables, _stock = book_of({0: 5.0})
        transfers = transfers_of((0, 1, 0, 40.0), (0, 2, 0, 1.0))
        refused, outcomes = self.run_batches(tables, transfers, moves_of(), [0, 1, 2], [0, 0, 0], True)
        self.assertEqual((refused, int(outcomes.row_count[0]), tables.money.balances.amount[0]), (1, 1, 5.0))

    def test_money_and_goods_of_one_batch_apply_together_or_not_at_all(self):
        tables, stock = book_of({0: 5.0})
        transfers = transfers_of((0, 1, 0, 1.0))
        moves = moves_of((0, 1, 0, 1, 1, 400.0))
        refused, outcomes = self.run_batches(tables, transfers, moves, [0, 1], [0, 1], False)
        self.assertEqual((refused, outcomes.code.tolist(), tables.money.balances.amount[0], stock.quantity(0, 0, 1)),
                         (1, [INSUFFICIENT_GOODS], 5.0, 10.0))

    def test_a_negative_amount_in_goods_is_refused_after_money_was_checked(self):
        tables, _stock = book_of({0: 5.0})
        refused, outcomes = self.run_batches(tables, transfers_of((0, 1, 0, 1.0)), moves_of((0, 1, 0, 1, 1, -1.0)), [0, 1], [0, 1],
                                             False)
        self.assertEqual((refused, outcomes.code.tolist(), outcomes.culprit.tolist()), (1, [NEGATIVE_QUANTITY], [0]))

    def test_a_negative_transfer_is_refused_before_any_overdraft_is_looked_for(self):
        tables, _stock = book_of({0: 0.0})
        _refused, outcomes = self.run_batches(tables, transfers_of((0, 1, 0, 9.0), (0, 1, 0, -1.0)), moves_of(), [0, 2], [0, 0],
                                              False)
        self.assertEqual((outcomes.code.tolist(), outcomes.culprit.tolist()), ([NEGATIVE_AMOUNT], [1]))


class ApplySettledTests(unittest.TestCase):
    def settle(self, tables, paid, given):
        scratch = scratch_for(4, 4)
        return apply_settled(tables, scratch, 0, numpy.array([0, 1]), numpy.array(paid), numpy.array([0.0, paid[0]]),
                             numpy.array([0]), numpy.array([1]), 0, numpy.array(given), numpy.array([0.0]))

    def test_a_settlement_pays_and_delivers_and_records(self):
        tables, stock = book_of({0: 10.0})
        self.assertEqual(self.settle(tables, [4.0, 0.0], [3.0]), (OK, -1))
        self.assertEqual((tables.money.balances.amount[0], tables.money.balances.amount[STRIDE], stock.quantity(0, 0, 1)),
                         (6.0, 4.0, 7.0))

    def test_an_overdrawn_payer_refuses_the_whole_settlement(self):
        tables, stock = book_of({0: 1.0})
        result = self.settle(tables, [4.0, 0.0], [3.0])
        self.assertEqual((result, stock.quantity(0, 0, 1)), ((INSUFFICIENT_FUNDS, 0), 10.0))

    def test_overdrawn_goods_refuse_after_the_money_passed(self):
        tables, _stock = book_of({0: 10.0})
        self.assertEqual(self.settle(tables, [4.0, 0.0], [30.0])[0], INSUFFICIENT_GOODS)


if __name__ == "__main__":
    unittest.main()
