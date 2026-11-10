"""The table after a year's service (`credit_service.apply_served`) and the change in principal it reports (`principal_changes`),
against the list `lending._collect` used to build: the loans not due where they were, then the loans still owed in id order; and the
dict `merchants_credit.stake` is given. Also which loans fall due (`due_rows`)."""

QUICK_TOPIC = True

import unittest

from sim.economy import credit_claims, credit_service
from sim.loans.store import LoanStore
from sim.tests import loans_plain
from sim.tests.loans_random import random_cash, random_loans

YEAR = 2
BANKS = ["bank:0"]


class ServiceTable(unittest.TestCase):
    def stand(self, seed: int):
        loans = random_loans(seed, 3 + seed % 20)
        store = LoanStore()
        store.append_contracts(loans)
        return loans, store, credit_service.due_rows(store, YEAR, BANKS)

    def test_loans_fall_due_a_year_after_they_were_struck_unless_the_borrower_is_a_bank(self):
        for seed in range(20):
            loans, _store, rows = self.stand(seed)
            self.assertEqual(rows.tolist(), [row for row, loan in enumerate(loans) if loan.issued_year < YEAR and loan.borrower not in BANKS])

    def test_the_table_is_the_untouched_loans_then_the_loans_still_owed_in_id_order(self):
        for seed in range(30):
            loans, store, rows = self.stand(seed)
            due = [loans[row] for row in rows.tolist()]
            cash = {loan.borrower: random_cash(seed)[loan.borrower] for loan in due if loan.borrower in random_cash(seed)}
            _transfers, serviced, _defaults, _receipts = loans_plain.service_split(due, cash, YEAR)
            untouched = [loan for row, loan in enumerate(loans) if row not in set(rows.tolist())]
            served = credit_service.serve(store, rows, cash)
            credit_service.apply_served(store, served, rows)
            self.assertEqual(store.snapshots(), untouched + serviced, "seed %d" % seed)

    def test_the_change_in_principal_is_what_the_python_dicts_gave(self):
        for seed in range(30):
            loans, store, rows = self.stand(seed)
            due = [loans[row] for row in rows.tolist()]
            cash = random_cash(seed)
            _transfers, serviced, _defaults, _receipts = loans_plain.service_split(due, cash, YEAR)
            before, after = credit_claims.principal_by_borrower(due), credit_claims.principal_by_borrower(serviced)
            wanted = {agent: after.get(agent, 0.0) - owed for agent, owed in before.items()}
            found = credit_service.principal_changes(store, credit_service.serve(store, rows, cash), rows)
            self.assertEqual(found, wanted)
            self.assertEqual(list(found), list(wanted))


if __name__ == "__main__":
    unittest.main()
