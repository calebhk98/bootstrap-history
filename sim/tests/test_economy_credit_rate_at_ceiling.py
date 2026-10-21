"""Complaint 641 diagnosis: which rule can put the cleared base rate at the lenders' ceiling. Each test builds
offers and requests and calls `credit.clear` or `lender_ask.lowest_ask`; none builds a game."""

QUICK_TOPIC = True

import unittest

from sim.economy import credit, lender_ask
from sim.economy.types import FundsOffer, LoanRequest

CEILING = 0.48          # four times a twelve percent opening rate (capital_market.RATE_CEILING_SHARE)


def request(borrower, amount, maximum_rate, collateral=1e9):
    return LoanRequest(borrower, "coin", amount, maximum_rate, 5.0, collateral, "working capital")


def funds(lender, amount, minimum_rate):
    return FundsOffer(lender, "coin", amount, minimum_rate)


def clear(requests, offers, last_rate=0.12, ceiling=CEILING):
    return credit.clear(requests, offers, "coin", last_rate, {}, rate_ceiling=ceiling)


class RateAtCeilingCandidateTests(unittest.TestCase):
    def test_demand_beyond_funds_at_every_rate_prices_at_the_marginal_borrowers_cap_not_the_lenders_ask(self):
        # lenders ask 0.10, funds 100; demand 300 from borrowers whose caps are all far above the ceiling:
        # a queue of buyers prices at their cap, so the rate runs to the ceiling with no lender asking for it
        offers = [funds("lender", 100.0, 0.10)]
        requests = [request("plant_a", 150.0, 1.5), request("plant_b", 150.0, 1.4)]
        target = credit.clearing_point([(0.10, 100.0)], [(1.5, 150.0), (1.4, 150.0)])
        self.assertGreater(target, CEILING)
        loans, rate, unmet = clear(requests, offers, last_rate=None)
        self.assertEqual(rate, CEILING)
        self.assertAlmostEqual(sum(loan.principal for loan in loans), 100.0)
        self.assertGreater(sum(left.amount for left in unmet), 0.0)

    def test_the_same_rationing_with_modest_caps_clears_below_the_ceiling(self):
        offers = [funds("lender", 100.0, 0.10)]
        requests = [request("plant_a", 150.0, 0.20), request("plant_b", 150.0, 0.18)]
        _loans, rate, _unmet = clear(requests, offers, last_rate=None)
        self.assertLess(rate, CEILING)

    def test_demand_within_funds_leaves_the_rate_at_the_lenders_ask(self):
        offers = [funds("lender", 500.0, 0.10)]
        _loans, rate, _unmet = clear([request("plant_a", 100.0, 1.5)], offers, last_rate=None)
        self.assertAlmostEqual(rate, 0.10)

    def test_a_lowest_ask_at_the_ceiling_needs_expected_inflation_and_loss_together(self):
        # time preference 0.05: a lender reaches 0.48 only with a 0.43 inflation expectation or loss record
        self.assertGreaterEqual(lender_ask.lowest_ask(0.05, 0.43), CEILING)
        self.assertLess(lender_ask.lowest_ask(0.05, 0.10, expected_loss_rate=0.10), CEILING)
        self.assertGreaterEqual(lender_ask.lowest_ask(0.05, 0.20, expected_loss_rate=lender_ask.loss_rate(0.25)),
                                CEILING)

    def test_every_ask_above_a_nominal_ceiling_lends_nothing_and_says_why_without_a_fake_rate(self):
        # nothing can clear at the bound: the rate is held (never the ceiling nobody accepts) and the cause is named
        offers = [funds("lender", 1000.0, 0.60)]
        result = credit.clear_with_cause([request("plant_a", 100.0, 1.5)], offers, "coin", 0.12, {},
                                         rate_ceiling=CEILING)
        self.assertEqual(result.cause, credit.NO_OFFER_AT_RATE)
        self.assertEqual(result.rate, 0.12)
        self.assertEqual(result.loans, [])
        self.assertAlmostEqual(sum(left.amount for left in result.unmet), 100.0)

    def test_the_bound_is_on_the_real_rate_so_expected_inflation_lets_the_ask_clear(self):
        # asks of 0.60 are time preference plus 0.55 expected inflation: real 0.05, under a real bound of 0.48
        offers = [funds("lender", 1000.0, 0.60)]
        loans, rate, unmet = credit.clear([request("plant_a", 100.0, 1.5)], offers, "coin", 0.12, {},
                                          rate_ceiling=CEILING, expected_inflation=0.55)
        self.assertAlmostEqual(rate, 0.60)
        self.assertAlmostEqual(sum(loan.principal for loan in loans), 100.0)
        self.assertEqual(unmet, [])

    def test_rationed_at_the_bound_the_least_risky_borrower_is_served_first(self):
        offers = [funds("lender", 100.0, 0.10)]
        safe = request("plant_a", 100.0, 3.0, collateral=1e9)
        risky = request("plant_b", 100.0, 5.0, collateral=0.0)      # the keener cap, but no collateral
        result = credit.clear_with_cause([risky, safe], offers, "coin", None, {}, rate_ceiling=CEILING)
        self.assertEqual(result.rate, CEILING)
        self.assertIsNone(result.cause)
        self.assertEqual({loan.borrower for loan in result.loans}, {"plant_a"})
        self.assertEqual([left.borrower for left in result.unmet], ["plant_b"])

    def test_a_cap_is_what_the_loan_earns_and_never_unbounded(self):
        self.assertAlmostEqual(credit.earnable_rate(30.0, 100.0), 0.30)
        for gain, outlay in ((1.0, 0.0), (float("inf"), 1.0), (float("nan"), 1.0), (-5.0, 10.0), (1.0, float("inf"))):
            self.assertEqual(credit.earnable_rate(gain, outlay), 0.0)

    def test_the_ceiling_clamp_hides_how_far_the_unclamped_clearing_point_lies(self):  # shape kept: the bound still binds
        offers = [funds("lender", 100.0, 0.10)]
        requests = [request("plant_a", 150.0, 3.0)]
        _loans, clamped, _unmet = clear(requests, offers, last_rate=None)
        _loans, free, _unmet = clear(requests, offers, last_rate=None, ceiling=None)
        self.assertEqual(clamped, CEILING)
        self.assertGreater(free, 2.0)


if __name__ == "__main__":
    unittest.main()
