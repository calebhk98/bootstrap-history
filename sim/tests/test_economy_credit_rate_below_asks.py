"""A sticky rate may not hold new loans below the price at which supply meets demand: where borrowers
who would pay more are rationed while lenders who would lend at that price sit out, the rate lifts to it."""

QUICK_TOPIC = True

import unittest

from sim.economy import credit
from sim.economy.types import FundsOffer, LoanRequest


def _glut_of_dear_funds_and_a_little_cheap():
    offers = [FundsOffer("cheap", "coin", 50.0, 0.01), FundsOffer("dear", "coin", 1000.0, 0.10)]
    requests = [LoanRequest("borrower", "coin", 500.0, 0.30, 10.0, 1e9, "working capital")]
    return requests, offers


class CreditRateBelowAsksTests(unittest.TestCase):
    def test_demand_beyond_the_cheap_lender_lifts_the_rate_to_the_next_ask(self):
        requests, offers = _glut_of_dear_funds_and_a_little_cheap()
        result = credit.clear_with_cause(requests, offers, "coin", 0.0, {})
        self.assertGreaterEqual(result.rate, 0.10)
        self.assertAlmostEqual(sum(loan.principal for loan in result.loans), 500.0)
        self.assertEqual(result.unmet, [])

    def test_every_lender_who_lends_asks_no_more_than_the_rate(self):
        requests, offers = _glut_of_dear_funds_and_a_little_cheap()
        result = credit.clear_with_cause(requests, offers, "coin", 0.0, {})
        asks = {offer.lender: offer.minimum_rate for offer in offers}
        for loan in result.loans:
            self.assertLessEqual(asks[loan.lender], result.rate + 1e-12)

    def test_a_glut_of_cheap_funds_still_lets_the_rate_fall_to_the_cheapest_ask(self):
        offers = [FundsOffer("cheap", "coin", 1000.0, 0.01), FundsOffer("dear", "coin", 1000.0, 0.10)]
        requests = [LoanRequest("borrower", "coin", 100.0, 0.30, 10.0, 1e9, "working capital")]
        result = credit.clear_with_cause(requests, offers, "coin", 0.2, {})
        self.assertAlmostEqual(result.rate, 0.01)

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

    def test_borrowers_who_cannot_pay_the_cheapest_ask_clear_nothing_and_say_so(self):
        requests = [LoanRequest("borrower", "coin", 100.0, 0.02, 10.0, 1e9, "working capital")]
        offers = [FundsOffer("saver", "coin", 1000.0, 0.10)]
        result = credit.clear_with_cause(requests, offers, "coin", 0.07, {})
        self.assertEqual(result.cause, credit.NO_BORROWER_AT_ASK)
        self.assertEqual(result.rate, 0.07)
        self.assertEqual(result.loans, [])


if __name__ == "__main__":
    unittest.main()
