"""The book's planning and recording kernels, which hold the tables' columns in hand instead of passing each table on whole
(`plan_transfers`, `plan_moves`, `record_moves`), against the plain versions they replaced, on seeded random batches; and the
hash start that spreads keys differing only in their high field."""
QUICK_TOPIC = True

import copy
import random
import unittest

import numpy

from sim.book_commit import record_moves
from sim.book_index import EMPTY, index_add, index_find, pack_key, start_position
from sim.book_plan import plan_moves, plan_transfers
from sim.tests import kernel_speed_plain as plain
from sim.tests.book_table_fixtures import (STRIDE, StockBook, agents_table, balances_table, moves_of, plan_and_index,
                                           transfers_of)

AGENTS = 6


def columns_of(table):
    return [numpy.asarray(column).tobytes() for column in table]


def random_transfers(rng):
    rows = [(rng.randrange(AGENTS), rng.randrange(AGENTS), rng.randrange(STRIDE), rng.choice([0.0, rng.uniform(0.0, 40.0)]))
            for _ in range(rng.randint(1, 12))]
    if rng.random() < 0.2:
        rows[rng.randrange(len(rows))] = (0, 1, 0, -1.0)
    return rows


def random_moves(rng):
    rows = [(rng.randrange(AGENTS), rng.randrange(AGENTS), rng.randrange(2), rng.randrange(3), rng.randrange(3),
             rng.choice([0.0, rng.uniform(0.0, 40.0)])) for _ in range(rng.randint(1, 12))]
    if rng.random() < 0.2:
        rows[rng.randrange(len(rows))] = (0, 1, 0, 0, 0, -1.0)
    return rows


class PlanKernelTests(unittest.TestCase):
    def test_plan_transfers_matches_the_plain_version(self):
        rng = random.Random(21)
        for _ in range(100):
            transfers = transfers_of(*random_transfers(rng))
            balances = balances_table(AGENTS, {rng.randrange(AGENTS * STRIDE): rng.uniform(0.0, 100.0) for _ in range(5)})
            (plan, local), (other_plan, other_local) = plan_and_index(30), plan_and_index(30)
            answer = plan_transfers(transfers, 0, len(transfers.amount), balances, STRIDE, plan, local)
            expected = plain.plan_transfers(transfers, 0, len(transfers.amount), balances, STRIDE, other_plan, other_local)
            self.assertEqual(tuple(map(int, answer)), tuple(map(int, expected)))
            self.assertEqual(columns_of(plan), columns_of(other_plan))
            self.assertEqual(local.tolist(), other_local.tolist())

    def test_plan_moves_matches_the_plain_version(self):
        rng = random.Random(22)
        for _ in range(100):
            book = StockBook(agents_table(*([0] * AGENTS)))
            for key in {(rng.randrange(AGENTS), rng.randrange(2), rng.randrange(3)) for _hold in range(6)}:
                book.hold(*key, rng.uniform(0.0, 50.0))
            moves = moves_of(*random_moves(rng))
            (plan, local), (other_plan, other_local) = plan_and_index(30), plan_and_index(30)
            answer = plan_moves(moves, 0, len(moves.quantity), book.stocks.table, book.stocks.index, plan, local)
            expected = plain.plan_moves(moves, 0, len(moves.quantity), book.stocks.table, book.stocks.index, other_plan, other_local)
            self.assertEqual(tuple(map(int, answer)), tuple(map(int, expected)))
            self.assertEqual(columns_of(plan), columns_of(other_plan))
            self.assertEqual(local.tolist(), other_local.tolist())


class RecordMovesTests(unittest.TestCase):
    def test_record_moves_matches_the_plain_version(self):
        rng = random.Random(23)
        for _ in range(100):
            book = StockBook(agents_table(*[rng.randrange(2) for _ in range(AGENTS)]))
            for table in (book.flows, book.edge_goods):
                table.reserve(30)
            moves = moves_of(*[row for row in random_moves(rng) if row[5] >= 0.0])
            for place in range(len(moves.quantity)):
                moves.purpose_code[place], moves.purpose_reference[place] = rng.randrange(3), rng.randrange(2)
            # rows made by an earlier batch exist, so both the found and the made path run
            earlier = moves_of(*[row for row in random_moves(rng) if row[5] >= 0.0])
            plain.record_moves(earlier, 0, len(earlier.quantity), book.tables())
            other = copy.deepcopy(book)
            count = len(moves.quantity)
            self.assertEqual(int(record_moves(moves, 0, count, book.tables())),
                             int(plain.record_moves(moves, 0, count, other.tables())))
            for name in ("flows", "edge_goods"):
                self.assertEqual(columns_of(getattr(book, name).table), columns_of(getattr(other, name).table))
                self.assertEqual(getattr(book, name).index.tolist(), getattr(other, name).index.tolist())
            self.assertEqual(columns_of(book.goods), columns_of(other.goods))

    def test_a_second_batch_adds_to_the_rows_the_first_made(self):
        book = StockBook(agents_table(1, 0, 0))
        for table in (book.flows, book.edge_goods):
            table.reserve(8)
        other = copy.deepcopy(book)
        first = moves_of((0, 1, 0, 0, 0, 3.0), (1, 2, 0, 0, 0, 1.5))
        second = moves_of((0, 1, 0, 0, 0, 0.25), (2, 0, 1, 0, 0, 4.0))
        for kernel, target in ((record_moves, book), (plain.record_moves, other)):
            kernel(first, 0, 2, target.tables())
            kernel(second, 0, 2, target.tables())
        self.assertEqual(columns_of(book.flows.table), columns_of(other.flows.table))
        self.assertEqual(columns_of(book.edge_goods.table), columns_of(other.edge_goods.table))


class HashStartTests(unittest.TestCase):
    def test_keys_that_differ_only_in_the_agent_start_in_different_places(self):
        size = 4096
        starts = {int(start_position(pack_key(agent, 7, 5), size)) for agent in range(300)}
        self.assertGreater(len(starts), 250)

    def test_every_key_is_found_whatever_the_load(self):
        rng = random.Random(24)
        keys = numpy.array(sorted({pack_key(rng.randrange(3000), rng.randrange(40), rng.randrange(9)) for _ in range(1500)}),
                           dtype=numpy.int64)
        index = numpy.full(4096, EMPTY, dtype=numpy.int64)
        for row in range(len(keys)):
            index_add(keys, index, row)
        self.assertEqual([int(index_find(keys, index, int(key))) for key in keys], list(range(len(keys))))
        self.assertEqual(int(index_find(keys, index, pack_key(5000, 1, 1))), EMPTY)


if __name__ == "__main__":
    unittest.main()
