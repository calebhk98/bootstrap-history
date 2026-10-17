"""Complaint 547: bids that cannot borrow are rationed demand and never set the rate; returned principal is
not the lender's income."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import credit, lending
from sim.economy.types import FundsOffer, Loan, LoanRequest

from sim.tests.test_economy_lending import MONEY, record_with


class RationedDemandTests(unittest.TestCase):
    def test_a_request_with_no_collateral_cannot_pull_the_rate_below_zero(self):
        asked = LoanRequest("b", "c", 100.0, 0.05, 2, 0.0, "x")
        loans, rate, unmet = credit.clear([asked], [FundsOffer("l", "c", 1000.0, 0.0)], "c", 0.01, {"b": 0.0})
        self.assertGreaterEqual(rate, 0.0)
        self.assertEqual(loans, [])
        self.assertEqual([(item.borrower, item.amount) for item in unmet], [("b", 100.0)])

    def test_rationed_requests_do_not_move_the_rate_others_clear_at(self):
        able = LoanRequest("able", "c", 100.0, 0.5, 2, 1.0e6, "x")
        barred = LoanRequest("barred", "c", 100.0, 0.05, 2, 0.0, "x")
        offers = [FundsOffer("l", "c", 1000.0, 0.02)]
        _loans, alone, _unmet = credit.clear([able], offers, "c", 0.05, {})
        loans, together, unmet = credit.clear([able, barred], offers, "c", 0.05, {})
        self.assertAlmostEqual(together, alone)
        self.assertEqual({loan.borrower for loan in loans}, {"able"})
        self.assertEqual([item.borrower for item in unmet], ["barred"])

    def test_requests_below_every_ask_are_unmet_and_the_rate_does_not_fall_under_the_ask(self):
        asked = LoanRequest("b", "c", 100.0, 0.04, 2, 1.0e6, "x")
        loans, rate, unmet = credit.clear([asked], [FundsOffer("l", "c", 1000.0, 0.05)], "c", 0.05, {})
        self.assertEqual(loans, [])
        self.assertGreaterEqual(rate, 0.05 - 1e-12)
        self.assertEqual(len(unmet), 1)


class ServiceSplitTests(unittest.TestCase):
    def one_loan(self, **changes):
        return dataclasses.replace(Loan("loan:1", "l", "b", MONEY, 100.0, 0.1, 4.0, 0.0, issued_year=1), **changes)

    def test_only_interest_is_the_lenders_income(self):
        record = record_with({"b": 1000.0, "l": 0.0})
        record.loans = [self.one_loan()]
        income = lending.service(record, MONEY, 2)
        self.assertAlmostEqual(income["l"], 10.0)

    def test_receipts_split_interest_principal_and_arrears(self):
        transfers, _updated, _defaults, receipts = credit.service_split(
            [self.one_loan(arrears=30.0, arrears_interest=5.0)], {"b": 1000.0}, 2)
        received = receipts["l"]
        self.assertAlmostEqual(received.interest, 10.0 + 5.0)
        self.assertAlmostEqual(received.principal, 25.0)
        self.assertAlmostEqual(received.arrears, 25.0)
        self.assertAlmostEqual(sum(transfer.amount for transfer in transfers),
                               received.interest + received.principal + received.arrears)

    def test_a_short_payment_goes_to_arrears_first_and_unpaid_interest_stays_interest(self):
        _transfers, updated, _defaults, receipts = credit.service_split(
            [self.one_loan(arrears=30.0, arrears_interest=5.0)], {"b": 20.0}, 2)
        self.assertAlmostEqual(receipts["l"].interest, 5.0)
        self.assertAlmostEqual(receipts["l"].principal, 0.0)
        self.assertAlmostEqual(receipts["l"].arrears, 15.0)
        # unpaid: 10 of arrears principal is paid down to 10; current interest 10 and installment 25 unpaid
        self.assertAlmostEqual(updated[0].arrears, 45.0)
        self.assertAlmostEqual(updated[0].arrears_interest, 10.0)


if __name__ == "__main__":
    unittest.main()
