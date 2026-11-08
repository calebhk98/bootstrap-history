"""The year ledger's kernels (sim/economy/year_ledger_kernels.py), each called on a handful of rows written out here, under numba
and under ROME_NO_JIT=1. A figure's entry order and the sums are what the dicts the ledger replaced gave."""

QUICK_TOPIC = True

import math
import random
import unittest

import numpy

from sim.economy import year_ledger_kernels as kernels, year_ledger_note_kernels as notes
from sim.economy.year_ledger_store import LedgerTables
from sim.economy.year_ledger_tables import (HOURS_SOLD, MONEY_OUT, OTHER_PURPOSE, SALES_PURPOSE, WAGES_PURPOSE, MEMBERS, NEXT_ENTRY)


def whole(*values):
    return numpy.array(values, dtype=numpy.int64)


def floats(*values):
    return numpy.array(values, dtype=numpy.float64)


def flags(*values):
    return numpy.array(values, dtype=numpy.bool_)


def tables_for(agents=8):
    """Tables with a row for each of `agents` agents (their numbers are 0 .. agents - 1)."""
    tables = LedgerTables()
    tables.book.agent_ids.admit(["agent%d" % number for number in range(agents)])
    tables.fit_agents()
    return tables


def entry_order(tables, figure_orders):
    """The agent numbers that are members, in the order they entered."""
    members = numpy.flatnonzero(figure_orders)
    return members[numpy.argsort(figure_orders[members])].tolist()


class ExactSumTests(unittest.TestCase):
    def test_matches_fsum_where_a_plain_sum_does_not(self):
        for values in ([0.1] * 10, [1e100, 1.0, -1e100], [], [-3.5, 2.25], [1e16, 1.0, 1.0, -1e16], [0.1, 0.2, 0.3, -0.6]):
            self.assertEqual(notes.exact_sum(floats(*values) if values else floats(), len(values)), math.fsum(values))

    def test_matches_fsum_on_random_lists(self):
        rng = random.Random(5)
        for _round in range(300):
            values = [rng.choice([1, -1]) * rng.uniform(0, 10) ** rng.randint(-8, 8) for _ in range(rng.randint(1, 40))]
            self.assertEqual(notes.exact_sum(floats(*values), len(values)), math.fsum(values))


class FigureKernelTests(unittest.TestCase):
    def test_adding_makes_a_member_that_keeps_its_place(self):
        tables = tables_for()
        figures, counters = tables.figures, tables.counters
        for agent, amount in ((3, 1.5), (1, 2.0), (3, 0.25)):
            kernels.add_to_figure(figures.money_out, figures.order_money_out, counters, MONEY_OUT, agent, amount)
        self.assertEqual(entry_order(tables, figures.order_money_out), [3, 1])
        self.assertEqual((figures.money_out[3], figures.money_out[1]), (1.75, 2.0))
        self.assertEqual((counters[2 * MONEY_OUT + NEXT_ENTRY], counters[2 * MONEY_OUT + MEMBERS]), (2, 2))

    def test_setting_replaces_the_figure_and_keeps_the_place(self):
        tables = tables_for()
        figures, counters = tables.figures, tables.counters
        kernels.add_to_figure(figures.hours_sold, figures.order_hours_sold, counters, HOURS_SOLD, 2, 5.0)
        kernels.add_to_figure(figures.hours_sold, figures.order_hours_sold, counters, HOURS_SOLD, 0, 1.0)
        kernels.set_figure(figures.hours_sold, figures.order_hours_sold, counters, HOURS_SOLD, 2, 9.0)
        self.assertEqual(entry_order(tables, figures.order_hours_sold), [2, 0])
        self.assertEqual(figures.hours_sold[2], 9.0)

    def test_removing_then_adding_enters_again_from_zero(self):
        tables = tables_for()
        figures, counters = tables.figures, tables.counters
        kernels.add_to_figure(figures.money_out, figures.order_money_out, counters, MONEY_OUT, 1, 4.0)
        kernels.add_to_figure(figures.money_out, figures.order_money_out, counters, MONEY_OUT, 2, 4.0)
        kernels.remove_from_figure(figures.order_money_out, counters, MONEY_OUT, 1)
        kernels.add_to_figure(figures.money_out, figures.order_money_out, counters, MONEY_OUT, 1, 1.0)
        self.assertEqual(entry_order(tables, figures.order_money_out), [2, 1])
        self.assertEqual(figures.money_out[1], 1.0)
        self.assertEqual(counters[2 * MONEY_OUT + MEMBERS], 2)

    def test_positive_only_skips_zero_and_negative_amounts(self):
        tables = tables_for()
        figures = tables.figures
        kernels.add_agent_amounts(figures.money_out, figures.order_money_out, tables.counters, MONEY_OUT, whole(0, 1, 2, 1),
                                  floats(0.0, 3.0, -1.0, 2.0), True)
        self.assertEqual(entry_order(tables, figures.order_money_out), [1])
        self.assertEqual(figures.money_out[1], 5.0)


class PairKernelTests(unittest.TestCase):
    def test_adding_to_a_row_sums_in_order_and_chains_the_agents_rows(self):
        tables = tables_for()
        store = tables.pairs["received"]
        store.reserve(4)
        target = store.target()
        for agent, good, amount in ((2, 5, 1.0), (1, 5, 2.0), (2, 6, 3.0), (2, 5, 0.5)):
            kernels.add_pair(target, agent, good, 0, amount, 0.0)
        rows = store.rows.table
        self.assertEqual(int(rows.row_count[0]), 3)
        self.assertEqual([(rows.agent[row], rows.subkey[row], rows.amount[row]) for row in range(3)], [(2, 5, 1.5), (1, 5, 2.0), (2, 6, 3.0)])
        self.assertEqual(store.chain_rows(2), [0, 2])
        self.assertEqual(entry_order(tables, tables.figures.order_received), [2, 1])

    def test_a_table_without_room_answers_minus_one(self):
        tables = tables_for()
        store = tables.pairs["sold"]
        store.reserve(1)
        target = store.target()
        capacity = int(store.rows.table.capacity[0])
        results = [kernels.add_pair(target, 0, good, 0, 1.0, 0.0) for good in range(capacity + 1)]
        self.assertEqual(results[-1], -1)
        self.assertEqual(int(store.rows.table.row_count[0]), capacity)

    def test_setting_a_row_replaces_both_figures(self):
        tables = tables_for()
        store = tables.pairs["hours_hired_by_market"]
        store.reserve(2)
        target = store.target()
        kernels.add_pair(target, 1, 4, 0, 10.0, 20.0)
        kernels.set_pair(target, 1, 4, 0, 3.0, 6.0)
        row = store.row_of(1, 4, 0)
        self.assertEqual((store.rows.table.amount[row], store.rows.table.second_amount[row]), (3.0, 6.0))

    def test_clearing_an_agent_kills_its_rows_and_keeps_the_agent_a_member(self):
        tables = tables_for()
        store = tables.pairs["hours_hired"]
        store.reserve(3)
        target = store.target()
        for agent, trade in ((1, 0), (1, 1), (2, 0)):
            kernels.add_pair(target, agent, trade, 0, 1.0, 0.0)
        kernels.clear_agent_rows(target, 1)
        self.assertEqual((store.row_of(1, 0, 0), store.row_of(1, 1, 0)), (-1, -1))
        self.assertEqual(store.row_of(2, 0, 0), 2)
        self.assertEqual(tables.figures.order_hours_hired[1] != 0, True)
        self.assertEqual(store.chain_rows(1), [])

    def test_a_killed_row_is_found_by_nothing_and_a_new_row_takes_its_key(self):
        tables = tables_for()
        store = tables.pairs["output"]
        store.reserve(3)
        target = store.target()
        kernels.add_pair(target, 0, 2, 0, 7.0, 0.0)
        kernels.kill_row(target, 0)
        self.assertEqual(int(kernels.find_pair(target, 0, 2, 0)), -1)
        kernels.add_pair(target, 0, 2, 0, 1.0, 0.0)
        self.assertEqual(int(kernels.find_pair(target, 0, 2, 0)), 1)


class SettlementKernelTests(unittest.TestCase):
    def test_money_goes_to_the_figures_its_purpose_names(self):
        tables = tables_for()
        figures = tables.figures
        notes.note_settlement_money(figures, tables.counters, whole(0, 1, 2, 3), floats(5.0, 0.0, 2.0, 0.0), floats(0.0, 4.0, 3.0, 6.0),
                                      flags(True, False, False, False), whole(SALES_PURPOSE, SALES_PURPOSE, WAGES_PURPOSE, OTHER_PURPOSE))
        self.assertEqual(figures.money_out[:4].tolist(), [5.0, 0.0, 2.0, 0.0])
        self.assertEqual(entry_order(tables, figures.order_money_out), [0, 2])
        self.assertEqual(entry_order(tables, figures.order_plant_spend), [0])
        self.assertEqual(entry_order(tables, figures.order_sales_in), [1])
        self.assertEqual(entry_order(tables, figures.order_wages_in), [2])

    def test_goods_count_only_in_sale_rows(self):
        tables = tables_for()
        for name in ("received", "sold"):
            tables.pairs[name].reserve(4)
        notes.note_settlement_goods(tables.pairs["received"].target(), tables.pairs["sold"].target(), whole(0, 1, 2), flags(True, False, True),
                                      floats(2.0, 0.0, 4.0), floats(0.0, 3.0, 1.0), whole(7, 7, 7),
                                      whole(SALES_PURPOSE, SALES_PURPOSE, WAGES_PURPOSE))
        received, sold = tables.pairs["received"], tables.pairs["sold"]
        self.assertEqual([(received.rows.table.agent[row], received.rows.table.amount[row]) for row in range(int(received.rows.table.row_count[0]))],
                         [(0, 2.0)])
        self.assertEqual([(sold.rows.table.agent[row], sold.rows.table.amount[row]) for row in range(int(sold.rows.table.row_count[0]))], [(1, 3.0)])

    def test_money_across_the_border_is_kept_under_the_purpose(self):
        tables = tables_for()
        for name in ("imports_paid", "exports_received"):
            tables.pairs[name].reserve(3)
        notes.note_settlement_foreign(tables.pairs["imports_paid"].target(), tables.pairs["exports_received"].target(), whole(0, 1),
                                        floats(4.0, 0.0), floats(0.0, 9.0), whole(3, 3), whole(5, 5))
        self.assertEqual(tables.pairs["imports_paid"].rows.table.amount[tables.pairs["imports_paid"].row_of(0, 3, 5)], 4.0)
        self.assertEqual(tables.pairs["exports_received"].rows.table.amount[tables.pairs["exports_received"].row_of(1, 3, 5)], 9.0)
        self.assertEqual(int(tables.pairs["imports_paid"].rows.table.row_count[0]), 1)


class LabourKernelTests(unittest.TestCase):
    def fills(self, tables, settled, paid_by, paid_to):
        for name in ("hours_hired", "hours_hired_by_market"):
            tables.pairs[name].reserve(4)
        notes.note_labour_fills(
            tables.figures, tables.counters, tables.pairs["hours_hired"].target(), tables.pairs["hours_hired_by_market"].target(),
            whole(0, 1, 1), whole(0, 0, 0), floats(100.0, 60.0, 60.0), floats(2.0, 2.0, 2.0), flags(True, False, False), whole(4, 4, 4),
            whole(9, 9, 9), floats(2.0, 2.0, 2.0), flags(settled, settled, settled), floats(*paid_by), floats(*paid_to))

    def test_fills_count_in_full_when_not_settled(self):
        tables = tables_for()
        self.fills(tables, False, (0.0,), (0.0,))
        hired = tables.pairs["hours_hired"]
        self.assertEqual(hired.rows.table.amount[hired.row_of(0, 4, 0)], 100.0)
        self.assertEqual(tables.figures.hours_sold[1], 120.0)
        by_market = tables.pairs["hours_hired_by_market"]
        row = by_market.row_of(0, 9, 0)
        self.assertEqual((by_market.rows.table.amount[row], by_market.rows.table.second_amount[row]), (100.0, 200.0))

    def test_settled_fills_count_only_as_far_as_the_wages_paid_cover_and_use_them_up(self):
        tables = tables_for()
        self.fills(tables, True, (100.0,), (100.0,))      # the employer paid for 50 hours at wage 2; the worker was paid for 50
        hired = tables.pairs["hours_hired"]
        self.assertEqual(hired.rows.table.amount[hired.row_of(0, 4, 0)], 50.0)
        self.assertEqual(tables.figures.hours_sold[1], 50.0)     # the first fill takes the 50 hours, the second finds nothing left


class RoundKernelTests(unittest.TestCase):
    def test_totals_weight_prices_by_quantity_and_use_what_was_delivered(self):
        tables = tables_for()
        delivered, order = numpy.zeros(4), numpy.zeros(4, dtype=numpy.int64)
        counters = numpy.zeros(4, dtype=numpy.int64)
        rounds = tables.rounds
        notes.add_rounds(rounds, delivered, order, counters, whole(2, 0, 2), floats(10.0, 5.0, 30.0), floats(1.0, 7.0, 2.0), floats(10.0, 5.0, 20.0))
        markets, quantity, price = notes.round_totals(rounds.market, rounds.quantity, rounds.price, int(rounds.row_count[0]), delivered, order, 4)
        self.assertEqual(markets.tolist(), [2, 0])                       # the order each market first had a round
        self.assertEqual(quantity.tolist(), [30.0, 5.0])                 # delivered, not matched
        self.assertEqual(price[0], (10.0 * 1.0 + 30.0 * 2.0) / 40.0)     # the rounds' prices weighted by what each matched
        self.assertEqual(price[1], 7.0)

    def test_a_market_with_nothing_delivered_keeps_its_last_price_and_none_is_nan(self):
        delivered, order = numpy.zeros(2), numpy.zeros(2, dtype=numpy.int64)
        markets, quantity, price = notes.round_totals(whole(1, 1), floats(4.0, 6.0), floats(3.0, numpy.nan), 2, delivered, order, 2)
        self.assertEqual((markets.tolist(), quantity.tolist()), ([1], [0.0]))
        self.assertTrue(math.isnan(price[0]))


if __name__ == "__main__":
    unittest.main()
