"""The loan store (`sim/loans/store.py`): what goes in comes out, the order of the loans is kept through every change, a loan's number
follows it, and the save records are those of the Contracts they replace."""

QUICK_TOPIC = True

import dataclasses
import unittest

import numpy

from sim.contracts import Contracts
from sim.loans.store import LoanStore
from sim.loans.view import LoanRow
from sim.tests.loans_random import random_loans


class LoanStoreTests(unittest.TestCase):
    def test_loans_come_back_as_they_went_in(self):
        loans = random_loans(1, 15)
        store = LoanStore()
        store.append_contracts(loans)
        self.assertEqual(store.snapshots(), loans)

    def test_the_records_are_the_contracts_fields_in_order(self):
        loans = random_loans(2, 10)
        store = LoanStore()
        store.append_contracts(loans)
        self.assertEqual(store.records(), [dataclasses.asdict(each) for each in loans])
        self.assertEqual([list(record) for record in store.records()], [[field.name for field in dataclasses.fields(each)] for each in loans])

    def test_loading_records_rebuilds_the_same_loans(self):
        loans = random_loans(3, 12)
        contracts = Contracts()
        contracts.load_records([dataclasses.asdict(each) for each in loans])
        self.assertEqual(contracts.loan_store.snapshots(), loans)
        self.assertEqual(contracts.to_records(facilities=False), [dataclasses.asdict(each) for each in loans])

    def test_retain_keeps_the_order_of_the_rest_and_a_loan_keeps_its_number(self):
        store = LoanStore()
        store.append_contracts(random_loans(4, 10))
        kept = LoanRow(store, store.number_of_row(6))
        before = kept.snapshot()
        keep = numpy.ones(10, dtype=numpy.bool_)
        keep[[1, 2, 8]] = False
        store.retain(keep)
        self.assertEqual(len(store), 7)
        self.assertEqual(kept.snapshot(), before)
        self.assertEqual(store.row_of(kept.number), 4)

    def test_a_loan_that_left_cannot_be_read(self):
        store = LoanStore()
        store.append_contracts(random_loans(5, 3))
        gone = LoanRow(store, store.number_of_row(0))
        store.retain(numpy.array([False, True, True]))
        with self.assertRaises(LookupError):
            gone.principal

    def test_a_write_through_a_row_changes_the_table_and_its_version(self):
        store = LoanStore()
        store.append_contracts(random_loans(6, 3))
        row = LoanRow(store, store.number_of_row(1))
        version = store.version
        row.principal = 12.5
        row.lender = "someone new"
        self.assertEqual(store.table.principal[1], 12.5)
        self.assertEqual(store.snapshot(1).lender, "someone new")
        self.assertGreater(store.version, version)

    def test_gather_reorders_and_drops(self):
        loans = random_loans(7, 6)
        store = LoanStore()
        store.append_contracts(loans)
        store.gather(numpy.array([4, 0, 2]))
        self.assertEqual(store.snapshots(), [loans[4], loans[0], loans[2]])

    def test_numbers_are_never_reused(self):
        store = LoanStore()
        store.append_contracts(random_loans(8, 4))
        numbers = store.table.number[:4].tolist()
        store.retain(numpy.array([False, False, False, False]))
        store.append_contracts(random_loans(9, 2))
        self.assertTrue(set(numbers).isdisjoint(store.table.number[:2].tolist()))

    def test_renaming_an_agent_renames_lenders_borrowers_and_ids_and_ends_loans_to_itself(self):
        contracts = Contracts()
        contracts.load_records([dataclasses.asdict(each) for each in random_loans(10, 14)])
        plain = Contracts()
        plain.load_records([dataclasses.asdict(each) for each in random_loans(10, 14)])
        contracts.rename("household:1", "household:2")
        wanted = [dataclasses.replace(each, lender=each.lender.replace("household:1", "household:2"),
                                      borrower=each.borrower.replace("household:1", "household:2"))
                  for each in plain.loan_store.snapshots()]
        self.assertEqual(contracts.loan_store.snapshots(), [each for each in wanted if each.lender != each.borrower])

    def test_replacing_all_loans_keeps_the_numbers_of_rows_that_stay(self):
        store = LoanStore()
        store.append_contracts(random_loans(11, 5))
        first = LoanRow(store, store.number_of_row(0))
        store.replace_all([first, random_loans(12, 1)[0]])
        self.assertEqual(len(store), 2)
        self.assertEqual(store.row_of(first.number), 0)


if __name__ == "__main__":
    unittest.main()
