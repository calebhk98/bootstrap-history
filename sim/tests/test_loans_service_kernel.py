"""`credit_service.serve` (the kernel `service_loans`) against the Python loop it replaced, on random loans and cash: the payments, the
loans still owed, the defaults and each lender's receipts are equal to the last bit, and the receipts come in the same order."""

QUICK_TOPIC = True

import unittest

import numpy

from sim.economy import credit, credit_service
from sim.loans.store import LoanStore
from sim.tests import loans_plain
from sim.tests.loans_random import random_cash, random_loans


class ServiceKernel(unittest.TestCase):
    def check(self, seed: int, count: int) -> None:
        loans, cash, year = random_loans(seed, count), random_cash(seed + 1000), 3
        expected = loans_plain.service_split(loans, cash, year)
        got = credit_service.service_split(loans, cash, year)
        for name, wanted, found in zip(("transfers", "loans", "defaults"), expected, got):
            self.assertEqual(found, wanted, "%s differ for seed %d" % (name, seed))
        self.assertEqual(list(got[3].items()), list(expected[3].items()), "receipts differ for seed %d" % seed)

    def test_random_loans_are_served_as_the_python_loop_served_them(self):
        for seed in range(40):
            self.check(seed, 1 + seed % 25)

    def test_no_loans_are_no_payments(self):
        self.assertEqual(credit_service.service_split([], {}, 1), ([], [], [], {}))

    def test_the_public_service_split_is_the_kernel(self):
        loans, cash = random_loans(7, 12), random_cash(8)
        self.assertEqual(credit.service_split(loans, cash, 2)[1], credit_service.service_split(loans, cash, 2)[1])

    def test_a_borrowers_cash_is_drawn_down_loan_by_loan_in_id_order(self):
        loans = random_loans(3, 2)
        for each in loans:
            each.borrower, each.arrears, each.arrears_interest, each.currency, each.rate, each.years_left = "b", 0.0, 0.0, "coin", 0.1, 1.0
            each.principal = 100.0
        loans[0].contract_id, loans[1].contract_id = "loan:z", "loan:a"
        store = LoanStore()
        store.append_contracts(loans)
        served = credit_service.serve(store, numpy.arange(2), {"b": 150.0})
        self.assertEqual(served.output.paid.tolist(), [110.0, 40.0])             # "loan:a" first: its row is 1, served first
        self.assertEqual(served.rows.tolist(), [1, 0])


if __name__ == "__main__":
    unittest.main()
