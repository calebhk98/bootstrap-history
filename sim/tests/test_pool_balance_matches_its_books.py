"""The lending pool holds the deposits it took less what it lent out, plus the interest it has received and not yet
shared; the savers' top-ups are repaid from what the pool holds beyond its lending (Complaint 586)."""

QUICK_TOPIC = True

import unittest

from sim.agents.purses import EDGE_OUTSIDE, EDGE_SAVERS, POOL
from sim.tests.test_pooled_lending import market

TOLERANCE = 1e-6
YEARS = 6


def books_gap(purses):
    """What the pool holds less what its books say it should: deposits less loans out, plus interest pending."""
    return purses.purse(POOL) - (purses.contracts.total_deposits() - purses.lent() + purses.interest_pending)


class PoolBalanceMatchesItsBooks(unittest.TestCase):
    def test_the_pool_balances_through_years_of_borrowing_to_pay_interest(self):
        state, lenders, borrowers = market(lender_count=2, borrower_count=2, cash=100.0, savers=1000.0)
        purses = state.purses
        for borrower in borrowers:
            purses.cover(borrower.account_id, 300.0)
        for _year in range(YEARS):
            for borrower in borrowers:
                purses.pay_interest(borrower.account_id, 0.3 * purses.debt(borrower.account_id))
            self.assertAlmostEqual(books_gap(purses), 0.0, delta=TOLERANCE)
            purses.settle_interest()
            self.assertAlmostEqual(books_gap(purses), 0.0, delta=TOLERANCE)
            self.assertAlmostEqual(purses.purse(POOL), purses.contracts.total_deposits() - purses.lent(), delta=TOLERANCE)
        self.assertTrue(purses.book.check_conservation(1e-9).ok)

    def test_interest_cash_is_not_lent_out_before_it_is_shared(self):
        state, _lenders, borrowers = market(lender_count=0, borrower_count=1, savers=1000.0)
        purses = state.purses
        borrower = borrowers[0].account_id
        purses.cover(borrower, 100.0)
        purses.pay_interest(borrower, 40.0)
        purses.cover(borrower, 500.0)   # a fresh draw while the interest waits in the pool
        paid = purses.settle_interest()
        self.assertAlmostEqual(sum(paid.values()), 40.0, delta=TOLERANCE)

    def test_the_savers_top_ups_are_repaid_from_excess(self):
        state, _lenders, borrowers = market(lender_count=0, borrower_count=1, savers=1000.0)
        purses = state.purses
        borrower = borrowers[0].account_id
        purses.cover(borrower, 400.0)
        self.assertAlmostEqual(purses.deposit(EDGE_SAVERS), 400.0)
        purses.transfer(EDGE_OUTSIDE, borrower, 250.0, "windfall")   # repays principal into the pool
        purses.settle_interest()
        self.assertAlmostEqual(purses.deposit(EDGE_SAVERS), purses.lent(), delta=TOLERANCE)
        self.assertAlmostEqual(purses.purse(POOL), 0.0, delta=TOLERANCE)


if __name__ == "__main__":
    unittest.main()
