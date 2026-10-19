"""The lending pool pays its depositors the interest it received and never more, pro rata to their deposits, so the
deposit rate is an outcome; a year in which borrowers pay little settles without error (Complaint 582)."""

QUICK_TOPIC = True

import unittest

from sim.agents.purses import EDGE_SAVERS, POOL
from sim.tests.test_pooled_lending import market

TOLERANCE_SHARE = 1e-9


def lent_market(interest, lender_count=2, cash=100.0, savers=1000.0):
    """A market with one borrower who has drawn and paid `interest` to the pool."""
    state, lenders, borrowers = market(lender_count, 1, cash=cash, savers=savers)
    borrower = borrowers[0].account_id
    state.purses.cover(borrower, 500.0)
    state.purses.pay_interest(borrower, interest)
    return state.purses, lenders


class PoolPaysWhatItReceived(unittest.TestCase):
    def test_little_interest_is_paid_out_exactly(self):
        purses, _lenders = lent_market(interest=1.0)
        paid = purses.settle_interest()
        self.assertAlmostEqual(sum(paid.values()), 1.0)

    def test_payments_are_pro_rata_to_deposits(self):
        purses, lenders = lent_market(interest=30.0)
        deposits = {account: purses.deposit(account) for account in [EDGE_SAVERS] + [lender.account_id for lender in lenders]}
        total = sum(deposits.values())
        paid = purses.settle_interest()
        for account, deposit in deposits.items():
            self.assertAlmostEqual(paid[account], 30.0 * deposit / total)

    def test_depositors_leaving_before_settlement_do_not_make_the_pool_overpay(self):
        purses, _lenders = lent_market(interest=50.0)
        purses.set_offers({EDGE_SAVERS: 1000.0})   # the lenders take their deposits back, draining the pool
        received = purses.purse(POOL)
        paid = purses.settle_interest()
        self.assertLessEqual(sum(paid.values()), received + 1e-9)
        self.assertGreaterEqual(purses.purse(POOL), -1e-9)

    def test_a_default_before_settlement_settles_and_the_book_conserves(self):
        purses, _lenders = lent_market(interest=20.0)
        purses.write_off(next(iter(purses.contracts.facilities)))
        paid = purses.settle_interest()
        self.assertLessEqual(sum(paid.values()), 20.0 + 1e-9)
        self.assertTrue(purses.book.check_conservation(TOLERANCE_SHARE).ok)


if __name__ == "__main__":
    unittest.main()
