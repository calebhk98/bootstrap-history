"""Complaint 641: the credit bound is on the real rate, borrowers' caps come from what the loan earns, and an entrant's
capital cost reads the cleared rate. Each test builds the inputs and calls the rule."""

QUICK_TOPIC = True

import types
import unittest

from sim.agents import entry_round
from sim.economy import credit, households_credit, lending
from sim.world import capital_market


def cohort(people, expected_inflation, last_year_income=1000.0):
    return types.SimpleNamespace(people=people, expected_inflation=expected_inflation, agent_id="c",
                                 last_year_income=last_year_income)


class RealRateBoundTests(unittest.TestCase):
    def test_the_market_bound_adds_the_inflation_lenders_expect(self):
        self.assertAlmostEqual(capital_market.bounded_rate(0.12, 9.0), 0.12 * capital_market.RATE_CEILING_SHARE)
        self.assertAlmostEqual(capital_market.bounded_rate(0.12, 9.0, expected_inflation=0.5),
                               0.12 * capital_market.RATE_CEILING_SHARE + 0.5)

    def test_expected_inflation_is_the_people_weighted_mean_of_cohorts(self):
        record = types.SimpleNamespace(cohorts={"a": cohort(300.0, 0.6), "b": cohort(100.0, 0.2)})
        self.assertAlmostEqual(lending.expected_inflation_of(record), 0.5)
        self.assertEqual(lending.expected_inflation_of(types.SimpleNamespace(cohorts={})), 0.0)


class CapsTests(unittest.TestCase):
    def test_a_household_cap_is_what_its_income_allows_with_no_typed_ceiling(self):
        asked = households_credit.subsistence_request(cohort(10.0, 0.0, 1.0e6), 100.0, "coin", 0.0, 0.0)
        self.assertIsNotNone(asked)
        service = households_credit.HOUSEHOLD_SERVICE_SHARE * 1.0e6
        self.assertAlmostEqual(asked.maximum_rate, (service - 100.0 / households_credit.HOUSEHOLD_LOAN_YEARS) / 100.0)
        self.assertGreater(asked.maximum_rate, 0.5)

    def test_a_run_with_no_cost_to_divide_by_asks_no_unbounded_cap(self):
        self.assertEqual(credit.earnable_rate(5.0, 0.0), 0.0)


class EntrantCapitalCostTests(unittest.TestCase):
    def test_a_loan_costs_at_least_the_cleared_rate(self):
        self.assertAlmostEqual(entry_round.capital_cost(0.0, 100.0, 0.64, 0.5), 64.0)

    def test_a_loan_above_the_market_costs_its_own_rate_and_pooled_money_the_market(self):
        self.assertAlmostEqual(entry_round.capital_cost(100.0, 100.0, 0.64, 0.7), 64.0 + 70.0)

    def test_no_borrowing_adds_no_loan_cost(self):
        self.assertAlmostEqual(entry_round.capital_cost(100.0, 0.0, 0.64, 9.0), 64.0)


if __name__ == "__main__":
    unittest.main()
