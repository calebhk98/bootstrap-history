"""The rate aims at the price where supply meets demand and moves toward it by the declared share of the gap each year; loans
clear at the rate it has reached, so lenders asking more than that sit out until it gets there."""

QUICK_TOPIC = True

import unittest

from sim.economy import credit
from sim.economy.types import FundsOffer, LoanRequest


def _glut_of_dear_funds_and_a_little_cheap():
    offers = [FundsOffer("cheap", "coin", 50.0, 0.01), FundsOffer("dear", "coin", 1000.0, 0.10)]
    requests = [LoanRequest("borrower", "coin", 500.0, 0.30, 10.0, 1e9, "working capital")]
    return requests, offers


class CreditRateBelowAsksTests(unittest.TestCase):
    def test_demand_beyond_the_cheap_lender_moves_the_rate_toward_the_crossing_between_the_asks(self):
        requests, offers = _glut_of_dear_funds_and_a_little_cheap()
        result = credit.clear_with_cause(requests, offers, "coin", 0.0, {})
        crossing = 0.01 + 0.09 * (500.0 - 50.0) / 1000.0
        self.assertAlmostEqual(result.rate, credit.RATE_ADJUSTMENT_SHARE_PER_YEAR * crossing)
        self.assertAlmostEqual(sum(loan.principal for loan in result.loans), 50.0)      # only the cheap lender asks no more than that
        self.assertAlmostEqual(sum(left.amount for left in result.unmet), 450.0)

    def test_a_rate_that_has_reached_the_crossing_lends_what_the_lenders_below_it_hold(self):
        requests, offers = _glut_of_dear_funds_and_a_little_cheap()
        crossing = 0.01 + 0.09 * (500.0 - 50.0) / 1000.0
        result = credit.clear_with_cause(requests, offers, "coin", crossing, {})
        self.assertAlmostEqual(result.rate, crossing)
        self.assertAlmostEqual(sum(loan.principal for loan in result.loans), 50.0)

    def test_every_lender_who_lends_asks_no_more_than_the_rate(self):
        requests, offers = _glut_of_dear_funds_and_a_little_cheap()
        result = credit.clear_with_cause(requests, offers, "coin", 0.0, {})
        asks = {offer.lender: offer.minimum_rate for offer in offers}
        for loan in result.loans:
            self.assertLessEqual(asks[loan.lender], result.rate + 1e-12)

    def test_a_glut_of_cheap_funds_lets_the_rate_fall_toward_the_cheapest_ask_by_the_declared_share(self):
        offers = [FundsOffer("cheap", "coin", 1000.0, 0.01), FundsOffer("dear", "coin", 1000.0, 0.10)]
        requests = [LoanRequest("borrower", "coin", 100.0, 0.30, 10.0, 1e9, "working capital")]
        result = credit.clear_with_cause(requests, offers, "coin", 0.2, {})
        self.assertAlmostEqual(result.rate, 0.2 + credit.RATE_ADJUSTMENT_SHARE_PER_YEAR * (0.01 - 0.2))

    def test_borrowers_with_no_lenders_are_no_price_so_the_held_rate_comes_back_with_a_cause(self):
        requests = [LoanRequest("borrower", "coin", 100.0, 0.80, 10.0, 1e9, "working capital")]
        result = credit.clear_with_cause(requests, [], "coin", 0.06, {})
        self.assertEqual(result.cause, credit.NO_OFFERS)
        self.assertEqual(result.rate, 0.06)
        self.assertEqual(result.loans, [])

    def test_no_held_rate_and_no_lenders_gives_no_rate_not_zero(self):
        requests = [LoanRequest("borrower", "coin", 100.0, 0.80, 10.0, 1e9, "working capital")]
        result = credit.clear_with_cause(requests, [], "coin", None, {})
        self.assertIsNone(result.rate)

    def test_borrowers_who_cannot_pay_the_cheapest_ask_clear_nothing_and_the_rate_drifts_toward_the_ask(self):
        requests = [LoanRequest("borrower", "coin", 100.0, 0.02, 10.0, 1e9, "working capital")]
        offers = [FundsOffer("saver", "coin", 1000.0, 0.10)]
        result = credit.clear_with_cause(requests, offers, "coin", 0.07, {})
        self.assertEqual(result.cause, credit.NO_BORROWER_AT_ASK)
        self.assertAlmostEqual(result.rate, 0.07 + credit.RATE_ADJUSTMENT_SHARE_PER_YEAR * (0.10 - 0.07))
        self.assertEqual(result.loans, [])


if __name__ == "__main__":
    unittest.main()
