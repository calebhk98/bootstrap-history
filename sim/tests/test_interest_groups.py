"""Complaint 110: the state's answer to an interest group is decided by its capacity and its purse, and the group's
claim reaches the budget as a requisition line and the levy rate through plain functions, called here on built inputs.
The groups a game's economy organises are in `test_interest_groups_scenario`."""

QUICK_TOPIC = True

import unittest

from sim.agents import budget
from sim.agents.group import state_response

CLAIM_NAME = "concession: group:displaced_producers:iron"
CLAIM_MONEY = 2500.0
VISIBLE_INCOME = 1.0e9


class StateResponse(unittest.TestCase):

    def test_a_state_with_more_capacity_makes_more_good_and_lets_more_blame_fall(self):
        weak = state_response(0.8, 0.2, False, "displaced_producers", 1.0e6)
        strong = state_response(0.8, 0.9, False, "displaced_producers", 1.0e6)
        self.assertGreater(strong["claim"], weak["claim"])
        self.assertGreater(strong["blame"], weak["blame"])

    def test_a_state_that_can_act_forbids_the_technique_when_the_pull_is_strong_enough(self):
        weak = state_response(0.8, 0.2, False, "displaced_producers", 1.0e6)
        strong = state_response(0.8, 0.9, False, "displaced_producers", 1.0e6)
        self.assertTrue(strong["ban"])
        self.assertFalse(weak["ban"])

    def test_a_state_in_deficit_compensates_instead_of_forbidding(self):
        response = state_response(0.8, 0.9, True, "displaced_producers", 1.0e6)
        self.assertFalse(response["ban"])
        self.assertGreater(response["claim"], 0.0)

    def test_employers_are_compensated_never_given_a_prohibition(self):
        self.assertFalse(state_response(0.9, 0.9, False, "squeezed_employers", 1.0e6)["ban"])


class ClaimInTheBudget(unittest.TestCase):

    def test_the_claim_is_a_requisition_line_of_the_standing_need_one_per_group(self):
        lines = budget.concession_lines({CLAIM_NAME: CLAIM_MONEY})
        self.assertEqual([line.name for line in lines], [CLAIM_NAME])
        self.assertEqual(lines[0].kind, "requisition")
        self.assertEqual(lines[0].money, CLAIM_MONEY)

    def test_a_levy_that_raises_an_unpaid_claim_sets_the_requisition_rate_from_the_income_the_state_sees(self):
        rates = budget.levy_rates({CLAIM_NAME: CLAIM_MONEY}, {CLAIM_NAME: "requisition"}, VISIBLE_INCOME)
        self.assertGreater(rates[0], 0.0)
        self.assertEqual(rates[1], 0.0)
        self.assertAlmostEqual(rates[0], CLAIM_MONEY / VISIBLE_INCOME, places=12)

    def test_a_claim_paid_in_full_adds_nothing_to_the_rate(self):
        self.assertEqual(budget.levy_rates({}, {CLAIM_NAME: "requisition"}, VISIBLE_INCOME), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
