"""Complaint 526: a state with a stated real programme that cannot hire the hours it planned for buys goods with the
rest, rather than leaving the coin it printed in its purse. Rules on built inputs; no economy is run."""

QUICK_TOPIC = True

import unittest

from sim.economy import state_budget
from sim.economy.types import Fill, LabourResult

STATE = "state"


def result(*fills):
    return LabourResult("labourer", "area", "coin", 1.0, 0.0, 0.0, 0.0, tuple(fills))


def fill(agent, hours, wage, side="buy"):
    return Fill(agent, "labourer", "area", "tile", hours, wage, side)


class WagesPaidTests(unittest.TestCase):
    def test_wages_paid_are_the_states_bought_hours_at_their_wage_across_the_trades(self):
        results = [result(fill(STATE, 10.0, 2.0), fill("firm", 5.0, 2.0), fill("household", 15.0, 2.0, "sell")),
                   result(fill(STATE, 4.0, 3.0))]
        self.assertEqual(state_budget.wages_paid(results, STATE), 32.0)

    def test_no_hours_bought_is_no_wages(self):
        self.assertEqual(state_budget.wages_paid([], STATE), 0.0)


class UnspentWagesTests(unittest.TestCase):
    def test_a_real_programme_moves_the_wage_budget_it_could_not_spend_to_goods(self):
        budget = state_budget.StateBudget(wage_budget=100.0, goods_budget=100.0, real_programme=True)
        state_budget.lapse_unspent_wages(budget, 30.0)
        self.assertEqual((budget.wage_budget, budget.goods_budget), (30.0, 170.0))

    def test_a_fully_spent_wage_budget_changes_nothing(self):
        budget = state_budget.StateBudget(wage_budget=100.0, goods_budget=100.0, real_programme=True)
        state_budget.lapse_unspent_wages(budget, 100.0)
        self.assertEqual((budget.wage_budget, budget.goods_budget), (100.0, 100.0))

    def test_a_budget_that_is_not_a_programme_keeps_its_unspent_cash(self):
        budget = state_budget.StateBudget(wage_budget=100.0, goods_budget=100.0, real_programme=False)
        state_budget.lapse_unspent_wages(budget, 30.0)
        self.assertEqual((budget.wage_budget, budget.goods_budget), (100.0, 100.0))


if __name__ == "__main__":
    unittest.main()
