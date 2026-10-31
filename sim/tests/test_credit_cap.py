"""A request whose premium at the full amount puts its ceiling under every ask is funded for what the collateral bears."""

QUICK_TOPIC = True

import unittest

from sim.economy import credit, credit_cap
from sim.economy.types import FundsOffer, LoanRequest


def premium_per_unit_of_collateral(debt_after, collateral_value, arrears):
    return 0.02 * debt_after / collateral_value


class FundableAmountTests(unittest.TestCase):
    def test_a_request_the_ceiling_allows_is_taken_whole(self):
        self.assertEqual(credit_cap.fundable_amount(100.0, 0.0, 1000.0, 0.0, 0.10, 0.05, premium_per_unit_of_collateral), 100.0)

    def test_a_request_past_the_collateral_is_cut_to_the_edge(self):
        # ceiling = 0.09 - 0.02 * amount / 100 meets 0.05 at amount 200
        taken = credit_cap.fundable_amount(1000.0, 0.0, 100.0, 0.0, 0.09, 0.05, premium_per_unit_of_collateral)
        self.assertAlmostEqual(taken, 200.0, places=6)

    def test_existing_debt_uses_up_the_room(self):
        taken = credit_cap.fundable_amount(1000.0, 150.0, 100.0, 0.0, 0.09, 0.05, premium_per_unit_of_collateral)
        self.assertAlmostEqual(taken, 50.0, places=6)

    def test_a_maximum_rate_under_the_ask_funds_nothing(self):
        self.assertEqual(credit_cap.fundable_amount(100.0, 0.0, 1000.0, 0.0, 0.04, 0.05, premium_per_unit_of_collateral), 0.0)


class ClearTests(unittest.TestCase):
    def test_clear_lends_what_the_collateral_bears_and_names_the_cause(self):
        requests = [LoanRequest("firm", "coin", 1000.0, 0.09, 1.0, 100.0, "working capital")]
        offers = [FundsOffer("saver", "coin", 5000.0, 0.05)]
        result = credit.clear_with_cause(requests, offers, "coin", 0.05, {})
        lent = sum(loan.principal for loan in result.loans)
        self.assertGreater(lent, 0.0)
        self.assertLess(lent, 1000.0)
        self.assertEqual(result.limited, {"firm": credit_cap.COLLATERAL_BOUND})
        self.assertAlmostEqual(sum(request.amount for request in result.unmet), 1000.0 - lent, places=6)


if __name__ == "__main__":
    unittest.main()
