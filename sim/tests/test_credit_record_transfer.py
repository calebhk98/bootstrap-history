"""CreditRecord.transfer_loan: a part of a loan bought by one buyer twice is two contracts with two ids."""

QUICK_TOPIC = True

import unittest

from sim.economy.credit_record import CreditRecord
from sim.economy.types import Loan


class TransferLoan(unittest.TestCase):
    def test_two_parcels_bought_by_one_buyer_have_different_ids(self):
        record = CreditRecord()
        loan = Loan("loan:1", "lender", "borrower", "coin", 100.0, rate=0.05, years_left=5.0)
        loan = record.add_loan(loan)
        record.transfer_loan(loan, "buyer", 0.2)
        record.transfer_loan(loan, "buyer", 0.25)
        identifiers = [each.loan_id for each in record.loans]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertAlmostEqual(sum(each.principal for each in record.loans), 100.0)

    def test_a_parcel_sold_on_to_the_same_buyer_keeps_ids_unique(self):
        record = CreditRecord()
        loan = Loan("loan:1", "lender", "borrower", "coin", 100.0, rate=0.05, years_left=5.0)
        loan = record.add_loan(loan)
        record.transfer_loan(loan, "buyer", 0.5)
        record.transfer_loan(loan, "buyer", 0.5)
        parcel = [each for each in record.loans if each.lender == "buyer"][0]
        record.transfer_loan(parcel, "buyer", 0.5)
        identifiers = [each.loan_id for each in record.loans]
        self.assertEqual(len(identifiers), len(set(identifiers)))


if __name__ == "__main__":
    unittest.main()
