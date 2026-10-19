"""A borrower with an empty purse draws its facility once for a batch of payments (interest to many lenders, wages
to many strata), so the lenders are asked once, not once per payment, and a year's cost does not grow with the
number of lender rows left by past years (Complaint 575)."""

QUICK_TOPIC = True

import unittest

from sim.agents import ledger, payroll
from sim.agents.api import ActorRecord, ActorsState
from sim.agents.firm import Firm
from sim.agents.purses import COIN, DEBT_FLOOR, EDGE_SAVERS


def lenders_and_borrower(lender_count):
    """A borrower with an empty purse and a facility held by `lender_count` firms that each offer funds."""
    state = ActorsState()
    purses = state.purses
    borrower = Firm("firm:borrower", ActorRecord(kind="firm"))
    lenders = [Firm("firm:lender%d" % index, ActorRecord(kind="firm", money=100.0)) for index in range(lender_count)]
    for actor in [borrower] + lenders:
        actor.attach(purses)
    purses.set_offers({EDGE_SAVERS: 1e6, **{lender.account_id: 100.0 for lender in lenders}})
    for lender in lenders:
        purses.contracts.draw(borrower.account_id, lender.account_id, COIN, 1.0)
    return state, borrower, lenders


def counting_draws(purses):
    calls = []
    original = purses._draw
    purses._draw = lambda borrower, shortfall: (calls.append(shortfall), original(borrower, shortfall))[1]
    return calls


class DrawsOncePerBatch(unittest.TestCase):
    def test_interest_to_many_lenders_draws_once_whatever_their_number(self):
        for lender_count in (3, 12, 40):
            state, borrower, _lenders = lenders_and_borrower(lender_count)
            draws = counting_draws(state.purses)
            received = state.purses.pay_interest(borrower.account_id, 6.0)
            self.assertEqual(len(draws), 1, lender_count)
            self.assertAlmostEqual(sum(received.values()), 6.0)

    def test_the_interest_is_drawn_in_full_when_the_purse_is_empty(self):
        state, borrower, _lenders = lenders_and_borrower(5)
        debt_before = state.purses.debt(borrower.account_id)
        state.purses.pay_interest(borrower.account_id, 6.0)
        self.assertAlmostEqual(state.purses.debt(borrower.account_id), debt_before + 6.0)
        self.assertAlmostEqual(state.purses.purse(borrower.account_id), 0.0)

    def test_wages_to_many_payees_draw_once(self):
        state, borrower, lenders = lenders_and_borrower(2)
        payees = [Firm("firm:payee%d" % index, ActorRecord(kind="firm")) for index in range(10)]
        for payee in payees:
            payee.attach(state.purses)
        draws = counting_draws(state.purses)
        payroll.share_out(borrower, payees, [1.0] * len(payees), 50.0, "wages")
        self.assertEqual(len(draws), 1)
        self.assertAlmostEqual(sum(state.purses.purse(payee.account_id) for payee in payees), 50.0)

    def test_a_lender_row_that_is_rounding_residue_is_dropped_on_repayment(self):
        state, borrower, lenders = lenders_and_borrower(3)
        contracts = state.purses.contracts
        contracts.facilities[borrower.account_id][lenders[0].account_id].principal = DEBT_FLOOR / 2
        contracts.tidy_facility(borrower.account_id, DEBT_FLOOR)
        self.assertNotIn(lenders[0].account_id, contracts.facility_of(borrower.account_id))
        self.assertEqual(len(contracts.facility_of(borrower.account_id)), 2)


if __name__ == "__main__":
    unittest.main()
