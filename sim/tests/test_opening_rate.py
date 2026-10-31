"""The opening solves its credit rate from the lenders' asks and the borrowers' requests; the typed starting rate is a
historical reference. Each test calls one function with written-out inputs."""
QUICK_TOPIC = True

import unittest

from sim.economy import credit
from sim.engine.opening_checks import rate_against_history
from sim.economy.opening_rate import against_history, solved_opening_rate
from sim.economy.types import LoanRequest
from sim.tests import finance_host


class SolvedOpeningRate(unittest.TestCase):
    def test_no_borrower_leaves_the_rate_at_the_lenders_lowest_ask(self):
        solved = solved_opening_rate([("a", 0.05, 0.0, 100.0), ("b", 0.08, 0.0, 100.0)], [])
        self.assertAlmostEqual(solved.rate, 0.05)
        self.assertEqual(solved.cause, credit.NO_BORROWER_AT_ASK)

    def test_lenders_with_no_funds_still_set_their_lowest_ask(self):
        self.assertAlmostEqual(solved_opening_rate([("a", 0.05, 0.02, 0.0)], []).rate, 0.07)

    def test_borrowers_who_can_pay_more_than_the_asks_clear_above_the_lowest_ask(self):
        lenders = [("a", 0.05, 0.0, 100.0)]
        requests = [LoanRequest("p", "opening", 300.0, 0.20, 1.0, 300.0, "capital")]
        solved = solved_opening_rate(lenders, requests)
        self.assertIsNone(solved.cause)
        self.assertGreaterEqual(solved.rate, 0.05)


class MarketRateBeforeCredit(unittest.TestCase):
    def test_the_finance_market_rate_is_the_solved_rate_not_the_typed_one(self):
        module = finance_host.build(civilisation={"starting_interest_rate": 0.31})
        self.assertAlmostEqual(module.market_rate(), 0.05)


class AgainstHistory(unittest.TestCase):
    def test_the_solved_rate_is_reported_beside_the_historical_one(self):
        self.assertEqual(against_history(0.05, 0.20), {"solved": 0.05, "historical": 0.20, "ratio": 0.25})


class RateAgainstHistory(unittest.TestCase):
    def test_a_solved_rate_a_quarter_of_the_typed_one_is_inside_the_band(self):
        result = rate_against_history(0.05, 0.20)
        self.assertEqual((result.value, result.passed), (0.25, True))

    def test_a_solved_rate_a_tenth_of_the_typed_one_is_outside_the_band(self):
        self.assertFalse(rate_against_history(0.02, 0.20).passed)

    def test_a_missing_figure_has_no_value_and_fails(self):
        result = rate_against_history(None, 0.20)
        self.assertEqual((result.value, result.passed), (None, False))


if __name__ == "__main__":
    unittest.main()
