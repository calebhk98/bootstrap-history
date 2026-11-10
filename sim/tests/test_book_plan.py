"""Planning a batch (sim/book_plan.py): the cells it touches, the value each would hold, and when it overdraws."""
QUICK_TOPIC = True

import unittest

from sim.book_index import pack_key
from sim.book_plan import (check_batch, check_one_payer, clear_plan, mark_overdrafts, plan_moves, plan_settled_money,
                           plan_settled_stock, plan_transfers)
from sim.book_tables import INSUFFICIENT_FUNDS, NEGATIVE_AMOUNT, NEGATIVE_QUANTITY
from sim.compiled_tables.causes import OK
from sim.tests.book_table_fixtures import (STRIDE, StockBook, agents_table, balances_table, moves_of, plan_and_index,
                                           transfers_of)


def cell(agent, currency=0):
    return agent * STRIDE + currency


class PlanTransfersTests(unittest.TestCase):
    def test_each_cell_is_planned_once_in_the_order_first_touched_with_running_values(self):
        balances = balances_table(3, {cell(0): 100.0, cell(1): 10.0})
        plan, local = plan_and_index(8)
        transfers = transfers_of((0, 1, 0, 30.0), (1, 2, 0, 5.0), (0, 1, 0, 20.0))
        self.assertEqual(plan_transfers(transfers, 0, 3, balances, STRIDE, plan, local), (OK, 0))
        rows = int(plan.row_count[0])
        self.assertEqual([plan.key[row] for row in range(rows)], [cell(0), cell(1), cell(2)])
        self.assertEqual([plan.before[row] for row in range(rows)], [100.0, 10.0, 0.0])
        self.assertEqual([plan.after[row] for row in range(rows)], [50.0, 55.0, 5.0])
        self.assertEqual([plan.moved[row] for row in range(rows)], [50.0, 55.0, 5.0])

    def test_the_first_negative_amount_is_refused_with_its_row(self):
        plan, local = plan_and_index(8)
        transfers = transfers_of((0, 1, 0, 3.0), (0, 1, 0, -1.0), (0, 1, 0, -2.0))
        self.assertEqual(plan_transfers(transfers, 0, 3, balances_table(2), STRIDE, plan, local), (NEGATIVE_AMOUNT, 1))

    def test_a_nan_amount_is_refused_like_a_negative_one(self):
        plan, local = plan_and_index(8)
        code, _row = plan_transfers(transfers_of((0, 1, 0, float("nan"))), 0, 1, balances_table(2), STRIDE, plan, local)
        self.assertEqual(code, NEGATIVE_AMOUNT)

    def test_the_same_agent_in_two_currencies_is_two_cells(self):
        plan, local = plan_and_index(8)
        plan_transfers(transfers_of((0, 1, 0, 1.0), (0, 1, 1, 2.0)), 0, 2, balances_table(2), STRIDE, plan, local)
        self.assertEqual(int(plan.row_count[0]), 4)

    def test_clear_plan_lets_the_next_batch_start_empty(self):
        plan, local = plan_and_index(8)
        plan_transfers(transfers_of((0, 1, 0, 1.0)), 0, 1, balances_table(2), STRIDE, plan, local)
        clear_plan(plan, local)
        plan_transfers(transfers_of((1, 0, 0, 4.0)), 0, 1, balances_table(2), STRIDE, plan, local)
        self.assertEqual([plan.key[row] for row in range(int(plan.row_count[0]))], [cell(1), cell(0)])


class OverdraftTests(unittest.TestCase):
    def plan_of(self, amounts, *rows, edges=(0, 0, 0)):
        balances = balances_table(3, amounts)
        plan, local = plan_and_index(8)
        transfers = transfers_of(*rows)
        plan_transfers(transfers, 0, len(rows), balances, STRIDE, plan, local)
        return plan, agents_table(*edges)

    def test_a_payer_who_would_end_below_zero_is_marked_failing(self):
        plan, agents = self.plan_of({cell(0): 10.0}, (0, 1, 0, 25.0))
        self.assertEqual((mark_overdrafts(plan, agents), plan.failing[0]), (1, 1))

    def test_an_edge_account_may_go_negative(self):
        plan, agents = self.plan_of({}, (0, 1, 0, 25.0), edges=(1, 0, 0))
        self.assertEqual(mark_overdrafts(plan, agents), 0)

    def test_a_shortfall_within_the_rounding_share_is_not_an_overdraft(self):
        plan, agents = self.plan_of({cell(0): 10.0}, (0, 1, 0, 10.0 * (1.0 + 1e-12)))
        self.assertEqual(mark_overdrafts(plan, agents), 0)

    def test_a_residue_already_below_zero_is_not_this_batchs_doing(self):
        plan, agents = self.plan_of({cell(0): -1e-3}, (1, 0, 0, 0.0))
        self.assertEqual(mark_overdrafts(plan, agents), 0)

    def test_a_batch_may_spend_money_it_receives_earlier_in_the_batch(self):
        plan, agents = self.plan_of({cell(0): 10.0}, (0, 1, 0, 10.0), (1, 2, 0, 10.0))
        self.assertEqual(mark_overdrafts(plan, agents), 0)

    def test_check_batch_names_the_cause_and_the_first_failing_cell(self):
        plan, agents = self.plan_of({cell(0): 1.0, cell(1): 1.0}, (0, 2, 0, 5.0), (1, 2, 0, 5.0))
        self.assertEqual(check_batch(plan, agents, INSUFFICIENT_FUNDS), (INSUFFICIENT_FUNDS, cell(0)))

    def test_a_single_posting_needs_the_payer_to_hold_the_amount_first(self):
        plan, agents = self.plan_of({cell(0): 4.0}, (0, 1, 0, 5.0))
        self.assertEqual(check_one_payer(plan, agents, 5.0, INSUFFICIENT_FUNDS), (INSUFFICIENT_FUNDS, cell(0)))

    def test_a_single_posting_from_an_edge_account_is_never_short(self):
        plan, agents = self.plan_of({}, (0, 1, 0, 5.0), edges=(1, 0, 0))
        self.assertEqual(check_one_payer(plan, agents, 5.0, INSUFFICIENT_FUNDS), (OK, 0))


class PlanMovesTests(unittest.TestCase):
    def test_the_receiver_is_planned_on_its_delivery_tile(self):
        book = StockBook(agents_table(0, 0))
        book.hold(0, 0, 5, 10.0)
        plan, local = plan_and_index(8)
        moves = moves_of((0, 1, 0, 5, 6, 4.0))
        self.assertEqual(plan_moves(moves, 0, 1, book.stocks.table, book.stocks.index, plan, local), (OK, 0))
        self.assertEqual([plan.key[row] for row in range(2)], [pack_key(0, 0, 5), pack_key(1, 0, 6)])
        self.assertEqual([plan.after[row] for row in range(2)], [6.0, 4.0])
        self.assertEqual([plan.slot[row] for row in range(2)], [0, -1])

    def test_a_negative_quantity_is_refused_with_its_row(self):
        book = StockBook(agents_table(0, 0))
        plan, local = plan_and_index(8)
        moves = moves_of((0, 1, 0, 5, 5, 1.0), (0, 1, 0, 5, 5, -1.0))
        self.assertEqual(plan_moves(moves, 0, 2, book.stocks.table, book.stocks.index, plan, local), (NEGATIVE_QUANTITY, 1))


class PlanSettledTests(unittest.TestCase):
    def test_settled_money_plans_balance_less_paid_plus_received_for_nonzero_entries_only(self):
        import numpy
        balances = balances_table(3, {cell(0): 100.0, cell(2): 7.0})
        plan, _local = plan_and_index(8)
        rows = plan_settled_money(numpy.array([0, 1, 2]), numpy.array([30.0, 0.0, 0.0]), numpy.array([5.0, 0.0, 2.0]), 0, STRIDE,
                                  balances, plan)
        self.assertEqual((rows, [plan.key[0], plan.key[1]], [plan.after[0], plan.after[1]], plan.moved[0]),
                         (2, [cell(0), cell(2)], [75.0, 9.0], 35.0))

    def test_settled_stock_plans_each_holder_and_tile_with_its_slot(self):
        import numpy
        book = StockBook(agents_table(0, 0))
        book.hold(0, 0, 3, 10.0)
        plan, _local = plan_and_index(8)
        rows = plan_settled_stock(numpy.array([0, 1]), numpy.array([3, 4]), 0, numpy.array([4.0, 0.0]), numpy.array([0.0, 4.0]),
                                  book.stocks.table, book.stocks.index, plan)
        self.assertEqual((rows, [plan.slot[0], plan.slot[1]], [plan.after[0], plan.after[1]]), (2, [0, -1], [6.0, 4.0]))


if __name__ == "__main__":
    unittest.main()
