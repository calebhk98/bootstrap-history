"""Complaint 546: a working-capital loan asked at a year's close must reach the producer before that year's plan, or it pays
for nothing it was asked for. `lending.lend_working_capital` strikes only those requests, dated to the last close so the one
payment falls due at this year's end, out of the households' cash above their targets. Called on a hand-built record; the
credit market and the lenders' asking rates are recorders. No game."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import lending, producers_close
from sim.economy.types import LoanRequest

MONEY = "coin"
YEAR = 7
ASKED = 50.0


def request(purpose, amount=ASKED, borrower="firm"):
    return LoanRequest(borrower, MONEY, amount, 0.5, 1.0, amount, purpose)


def record(requests, balances):
    """Two households whose cash targets are 200 each, holding `balances`; the book answers balances and records transfers."""
    book = types.SimpleNamespace(balance=lambda agent, money: balances[agent], transfer_many=mock.Mock())
    cohorts = {name: types.SimpleNamespace(cash_target=200.0, expected_inflation=0.0) for name in sorted(balances)}
    return types.SimpleNamespace(
        loan_requests=list(requests), loans=[], book=book, cohorts=cohorts, merchants={}, loss_rates={},
        remembered_defaults={}, memory=types.SimpleNamespace(rates={MONEY: 0.05}))


def lend(the_record, loans=()):
    setup = types.SimpleNamespace(currency_id=MONEY, opening_rate=0.1)
    clear = mock.Mock(return_value=(list(loans), 0.05, []))
    with mock.patch.object(lending, "credit", types.SimpleNamespace(
            clear=clear, disbursements=lambda made: ["paid:%s" % loan.borrower for loan in made])), \
            mock.patch.object(lending, "lender_ask", types.SimpleNamespace(lowest_ask=lambda *a, **k: 0.02, loss_rate=lambda x: 0.0)), \
            mock.patch.object(lending, "credit_claims", types.SimpleNamespace(
                principal_by_borrower=lambda loans: {}, arrears_history=lambda *a: {})), \
            mock.patch.object(lending, "merchants_credit") as merchants, \
            mock.patch.object(lending, "expected_inflation_of", return_value=0.0):
        lending.lend_working_capital(setup, the_record, types.SimpleNamespace(year=YEAR))
    return clear, merchants


class LendWorkingCapitalTests(unittest.TestCase):
    def test_only_the_working_capital_requests_go_to_the_credit_market(self):
        plant = request("plant", 5.0)
        the_record = record([request(producers_close.WORKING_CAPITAL_PURPOSE), plant], {"a": 500.0, "b": 100.0})
        clear, _merchants = lend(the_record)
        self.assertEqual([each.purpose for each in clear.call_args.args[0]], [producers_close.WORKING_CAPITAL_PURPOSE])
        self.assertEqual(the_record.loan_requests, [plant])

    def test_the_loan_is_dated_to_the_last_close_so_its_payment_falls_due_at_the_end_of_this_year(self):
        clear, _merchants = lend(record([request(producers_close.WORKING_CAPITAL_PURPOSE)], {"a": 500.0, "b": 100.0}))
        self.assertEqual(clear.call_args.kwargs["year"], YEAR - 1)

    def test_lenders_are_the_households_cash_above_their_targets(self):
        clear, _merchants = lend(record([request(producers_close.WORKING_CAPITAL_PURPOSE)], {"a": 500.0, "b": 100.0}))
        offers = clear.call_args.args[1]
        self.assertEqual([(offer.lender, offer.amount) for offer in offers], [("a", 300.0)])

    def test_the_loans_made_are_booked_paid_out_and_staked_to_a_merchant_borrower(self):
        loan = types.SimpleNamespace(borrower="firm", principal=ASKED)
        the_record = record([request(producers_close.WORKING_CAPITAL_PURPOSE)], {"a": 500.0, "b": 100.0})
        _clear, merchants = lend(the_record, [loan])
        self.assertEqual(the_record.loans, [loan])
        the_record.book.transfer_many.assert_called_once_with(["paid:firm"])
        merchants.stake.assert_called_once_with({}, {"firm": ASKED})

    def test_with_no_working_capital_request_nothing_is_cleared(self):
        plant = request("plant", 5.0)
        the_record = record([plant], {"a": 500.0, "b": 100.0})
        clear, _merchants = lend(the_record)
        clear.assert_not_called()
        self.assertEqual(the_record.loan_requests, [plant])

    def test_with_no_household_cash_above_target_the_requests_are_asked_of_nobody(self):
        the_record = record([request(producers_close.WORKING_CAPITAL_PURPOSE)], {"a": 100.0, "b": 100.0})
        clear, _merchants = lend(the_record)
        clear.assert_not_called()
        self.assertEqual(the_record.loan_requests, [])


if __name__ == "__main__":
    unittest.main()
