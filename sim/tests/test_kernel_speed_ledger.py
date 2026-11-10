"""The ledger's pair kernels, which add through the table's columns and make a row without passing the table on whole
(`add_pair`, `note_settlement_goods`, `note_labour_fills`), against the plain versions they replaced, on seeded random rows."""
QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.economy import year_ledger_kernels as kernels, year_ledger_note_kernels as notes
from sim.economy.year_ledger_store import LedgerTables
from sim.economy.year_ledger_tables import HOURS_SOLD, OTHER_PURPOSE, SALES_PURPOSE, WAGES_PURPOSE
from sim.tests import kernel_speed_plain as plain

AGENTS = 9


def ledger():
    tables = LedgerTables()
    tables.book.agent_ids.admit(["agent%d" % number for number in range(AGENTS)])
    tables.fit_agents()
    return tables


def columns_of(table):
    return [numpy.asarray(column).tobytes() for column in table]


def same_ledgers(test, first, second, names):
    for name in names:
        test.assertEqual(columns_of(first.pairs[name].rows.table), columns_of(second.pairs[name].rows.table))
        test.assertEqual(first.pairs[name].rows.index.tolist(), second.pairs[name].rows.index.tolist())
    test.assertEqual(columns_of(first.figures), columns_of(second.figures))
    test.assertEqual(first.counters.tolist(), second.counters.tolist())


class PairKernelTests(unittest.TestCase):
    def test_add_pair_matches_the_plain_version_in_a_chained_and_a_plain_table(self):
        rng = random.Random(31)
        for name in ("received", "output"):
            first, second = ledger(), ledger()
            for _ in range(200):
                row = (rng.randrange(AGENTS), rng.randrange(4), rng.randrange(2), rng.uniform(-3.0, 9.0), rng.uniform(0.0, 2.0))
                answers = []
                for tables, add in ((first, kernels.add_pair), (second, plain.add_pair)):
                    tables.pairs[name].reserve(1)
                    answers.append(int(add(tables.pairs[name].target(), *row)))
                self.assertEqual(answers[0], answers[1])
            same_ledgers(self, first, second, (name,))


class NoteKernelTests(unittest.TestCase):
    def test_note_settlement_goods_matches_the_plain_version(self):
        rng = random.Random(32)
        for _ in range(60):
            rows = rng.randint(1, 40)
            agents = numpy.array([rng.randrange(AGENTS) for _ in range(rows)], dtype=numpy.int64)
            got = numpy.array([rng.random() < 0.6 for _ in range(rows)])
            goods_in = numpy.array([rng.uniform(0.0, 5.0) for _ in range(rows)])
            goods_out = numpy.array([rng.choice([0.0, rng.uniform(0.0, 5.0)]) for _ in range(rows)])
            good = numpy.array([rng.randrange(5) for _ in range(rows)], dtype=numpy.int64)
            kind = numpy.array([rng.choice([SALES_PURPOSE, SALES_PURPOSE, OTHER_PURPOSE, WAGES_PURPOSE]) for _ in range(rows)],
                               dtype=numpy.int64)
            first, second = ledger(), ledger()
            for tables in (first, second):
                for name in ("received", "sold"):
                    tables.pairs[name].reserve(rows)
            notes.note_settlement_goods(first.pairs["received"].target(), first.pairs["sold"].target(), agents, got, goods_in,
                                        goods_out, good, kind)
            received, sold = second.pairs["received"].target(), second.pairs["sold"].target()
            for place in range(rows):
                if kind[place] != SALES_PURPOSE:
                    continue
                if got[place]:
                    plain.add_pair(received, agents[place], good[place], 0, goods_in[place], 0.0)
                if goods_out[place] > 0.0:
                    plain.add_pair(sold, agents[place], good[place], 0, goods_out[place], 0.0)
            same_ledgers(self, first, second, ("received", "sold"))

    def test_note_labour_fills_matches_the_plain_version(self):
        rng = random.Random(33)
        for _ in range(60):
            rows = rng.randint(1, 40)
            agent = numpy.array([rng.randrange(AGENTS) for _ in range(rows)], dtype=numpy.int64)
            slot = numpy.array([rng.randrange(3) for _ in range(rows)], dtype=numpy.int64)
            quantity = numpy.array([rng.uniform(1.0, 90.0) for _ in range(rows)])
            price = numpy.array([rng.uniform(0.5, 4.0) for _ in range(rows)])
            is_buy = numpy.array([rng.random() < 0.5 for _ in range(rows)])
            trade = numpy.array([rng.randrange(3) for _ in range(rows)], dtype=numpy.int64)
            market = numpy.array([rng.randrange(4) for _ in range(rows)], dtype=numpy.int64)
            wage = numpy.array([rng.uniform(0.5, 4.0) for _ in range(rows)])
            settled = numpy.array([rng.random() < 0.5 for _ in range(rows)])
            paid = [numpy.array([rng.uniform(0.0, 200.0) for _ in range(3)]) for _ in range(2)]
            first, second = ledger(), ledger()
            for tables in (first, second):
                for name in ("hours_hired", "hours_hired_by_market"):
                    tables.pairs[name].reserve(rows)
            notes.note_labour_fills(first.figures, first.counters, first.pairs["hours_hired"].target(),
                                    first.pairs["hours_hired_by_market"].target(), agent, slot, quantity, price, is_buy, trade,
                                    market, wage, settled, paid[0].copy(), paid[1].copy())
            hired, by_market = second.pairs["hours_hired"].target(), second.pairs["hours_hired_by_market"].target()
            paid_by, paid_to = paid[0].copy(), paid[1].copy()
            for place in range(rows):
                hours = quantity[place]
                if settled[place]:
                    purse = paid_by if is_buy[place] else paid_to
                    hours = notes.paid_hours(hours, wage[place], purse, slot[place])
                if is_buy[place]:
                    plain.add_pair(hired, agent[place], trade[place], 0, hours, 0.0)
                    plain.add_pair(by_market, agent[place], market[place], 0, hours, hours * price[place])
                else:
                    kernels.add_to_figure(second.figures.hours_sold, second.figures.order_hours_sold, second.counters,
                                          HOURS_SOLD, agent[place], hours)
            same_ledgers(self, first, second, ("hours_hired", "hours_hired_by_market"))


if __name__ == "__main__":
    unittest.main()
