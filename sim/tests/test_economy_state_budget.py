"""The state's budget survives a save: a year's `state_budget` (revenue, the wage and goods budgets, what it financed) comes
back equal from `EconomyRecord.to_record` / `from_record`, and an economy resumed from it plans the same year. Called on
the engine-free fixture economy. The financing order, debasing, bids for hours and goods and conservation are rules in
test_economy_agent_state; how the budget behaves over years on an opened England is measured by
`python3 sim/simulator.py economy-check --civs england_1300 --years 8`."""
QUICK_TOPIC = True

import unittest

from sim.economy.economy import Economy
from sim.economy.record import EconomyRecord
from sim.economy.state_policy import StatePolicy
from sim.tests import economy_fixture as fixture

COIN = "coin"


def stepped(years=2):
    economy = Economy(fixture.small_setup(state_policy=StatePolicy(financing_order=("issue",))))
    for _year in range(years):
        economy.step(fixture.quiet_year(economy.setup))
    return economy


class StateBudgetRecordTests(unittest.TestCase):
    def test_the_budget_round_trips_through_the_save(self):
        economy = stepped()
        again = EconomyRecord.from_record(economy.record.to_record())
        self.assertEqual(again.state_budget, economy.record.state_budget)

    def test_the_round_trip_is_not_trivial(self):
        budget = stepped().record.state_budget
        self.assertGreater(budget.wage_budget + budget.goods_budget, 0.0)

    def test_an_economy_resumed_from_the_save_plans_the_same_next_year(self):
        economy = stepped()
        resumed = Economy(economy.setup, EconomyRecord.from_record(economy.record.to_record()))
        economy.step(fixture.quiet_year(economy.setup))
        resumed.step(fixture.quiet_year(resumed.setup))
        self.assertEqual(resumed.record.state_budget, economy.record.state_budget)


if __name__ == "__main__":
    unittest.main()
