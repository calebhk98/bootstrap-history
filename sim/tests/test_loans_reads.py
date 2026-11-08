"""The per-agent reads of the loan table (`sim/loans/reads.py`) against the Python loops of `credit_claims` over the same loans as
objects: the same dicts, the same keys in the same order, the same floats."""

QUICK_TOPIC = True

import unittest

from sim.economy import credit_claims
from sim.economy.credit_record import CreditRecord
from sim.tests.loans_random import random_loans


def both(seed: int, count: int):
    loans = random_loans(seed, count)
    credit = CreditRecord()
    credit.add_loans(loans)
    return loans, credit.loans


class LoanReads(unittest.TestCase):
    def same(self, function, *arguments) -> None:
        for seed in range(30):
            loans, rows = both(seed, 1 + seed % 20)
            wanted, found = function(loans, *arguments), function(rows, *arguments)
            self.assertEqual(found, wanted)
            self.assertEqual(list(found), list(wanted))

    def test_claims_by_lender(self):
        self.same(credit_claims.claims_by_lender)
        self.same(credit_claims.claims_by_lender, "coin")
        self.same(credit_claims.claims_by_lender, "silver")

    def test_debts_by_borrower(self):
        self.same(credit_claims.debts_by_borrower)
        self.same(credit_claims.debts_by_borrower, "gold")

    def test_principal_by_borrower(self):
        self.same(credit_claims.principal_by_borrower)

    def test_arrears_history_starts_from_the_losses_remembered(self):
        remembered = {"household:1": 7.5, "stranger": 2.0, "producer:3": 0.25}
        self.same(credit_claims.arrears_history, remembered)

    def test_an_empty_table_reads_nothing(self):
        rows = CreditRecord().loans
        self.assertEqual(credit_claims.claims_by_lender(rows), {})
        self.assertEqual(credit_claims.arrears_history(rows, {"a": 1.0}), {"a": 1.0})


if __name__ == "__main__":
    unittest.main()
