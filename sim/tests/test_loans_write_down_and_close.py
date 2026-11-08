"""The write-off kernel and the close's loan loop (`sim/loans/write_down_kernel.py`, `close_kernel.py`) against the Python they replaced."""

QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.economy import firm_finance
from sim.economy.loan_write_offs import LoanWriteOffs
from sim.economy.credit_record import CreditRecord
from sim.loans.close_kernel import producer_loans
from sim.loans.store import LoanStore
from sim.loans.write_down_kernel import new_outputs, write_down
from sim.tests import loans_plain
from sim.tests.loans_random import AGENTS, random_loans


class WriteDown(unittest.TestCase):
    def test_each_loan_loses_its_ratio_as_written_down_does(self):
        for seed in range(25):
            loans = random_loans(seed, 1 + seed % 15)
            rng = random.Random(seed)
            ratios = [rng.choice((0.0, 0.25, 1.0, rng.random())) for _loan in loans]
            store = LoanStore()
            store.append_contracts(loans)
            lost, remains = new_outputs(len(loans))
            write_down(store.table, numpy.arange(len(loans)), numpy.array(ratios), firm_finance.ARREARS_EPSILON, lost, remains)
            for row, (loan, ratio) in enumerate(zip(loans, ratios)):
                written, wanted_loss = loans_plain.written_down(loan, ratio)
                self.assertEqual(store.snapshot(row), written)
                self.assertEqual(float(lost[row]), wanted_loss)
                self.assertEqual(bool(remains[row]), written.principal > firm_finance.ARREARS_EPSILON or written.arrears > firm_finance.ARREARS_EPSILON)

    def test_a_flush_drops_the_loans_written_to_nothing_and_books_the_losses(self):
        credit = CreditRecord()
        credit.add_loans(random_loans(5, 12))
        record = type("Record", (), {"credit": credit})()
        borrowers = sorted({loan.borrower for loan in credit.loans})
        lost = LoanWriteOffs(record).apply({borrowers[0]: 1.0, borrowers[1]: 0.5, "nobody": 0.5})
        self.assertEqual(set(lost), {borrowers[0], borrowers[1], "nobody"})
        self.assertEqual(lost["nobody"], 0.0)
        self.assertEqual([loan for loan in credit.loans if loan.borrower == borrowers[0]], [])


class CloseLoop(unittest.TestCase):
    def test_a_producers_figures_are_the_loans_added_in_table_order(self):
        for seed in range(25):
            loans = random_loans(seed, 1 + seed % 20)
            producers = {agent: row for row, agent in enumerate(AGENTS[6:12])}
            store = LoanStore()
            store.append_contracts(loans)
            producer_row = numpy.array([producers.get(name, -1) for name in store.agents.name_list], dtype=numpy.int64)
            got = tuple(numpy.zeros(len(producers)) for _name in range(4))
            producer_loans(store.table, len(store), producer_row, *got)
            for found, wanted in zip(got, loans_plain.producer_loans(loans, producers, len(producers))):
                self.assertEqual(found.tolist(), wanted.tolist())


if __name__ == "__main__":
    unittest.main()
