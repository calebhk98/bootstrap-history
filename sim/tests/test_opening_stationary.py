"""Rules of `sim/economy/opening_stationary.py` on built inputs: the runs, hours and incomes of a year that repeats."""

QUICK_TOPIC = True

import unittest

from sim.economy import opening_stationary
from sim.tests import economy_fixture as fixture

WAGES = {fixture.LABOURER: 1.0, fixture.MINER: 1.2, fixture.SMITH: 1.5}
PRICES = {fixture.GRAIN: 0.3, fixture.ORE: 0.05, fixture.METAL: 95.0}
RATE = 0.06


def solve(final):
    return opening_stationary.solve({fixture.TOWN: final}, fixture.recipes(), PRICES, WAGES, RATE)


class RunsAndHoursTests(unittest.TestCase):
    def test_grain_for_people_takes_runs_and_hours_of_the_farm_alone(self):
        flows = solve({fixture.GRAIN: 2_000_000.0})
        self.assertAlmostEqual(flows.runs[fixture.FARM], 2000.0)
        self.assertAlmostEqual(flows.hours_by_trade[fixture.LABOURER], 2000.0 * 300.0)
        self.assertNotIn(fixture.MINE, flows.runs)

    def test_a_metal_demand_takes_the_smelter_and_the_ore_it_burns(self):
        flows = solve({fixture.METAL: 10.0})
        self.assertAlmostEqual(flows.runs[fixture.SMELT], 10.0)
        self.assertAlmostEqual(flows.runs[fixture.MINE], 10.0)
        self.assertAlmostEqual(flows.hours_by_trade[fixture.SMITH], 300.0)
        self.assertAlmostEqual(flows.hours_by_trade[fixture.MINER], 400.0)

    def test_the_wage_bill_is_hours_at_each_trades_wage(self):
        flows = solve({fixture.METAL: 10.0})
        self.assertAlmostEqual(flows.wage_bill, 300.0 * 1.5 + 400.0 * 1.2)


class IncomeIdentityTests(unittest.TestCase):
    def test_wages_plus_profit_equal_the_value_of_final_demand_at_any_prices(self):
        for prices in (PRICES, {fixture.GRAIN: 0.9, fixture.ORE: 0.001, fixture.METAL: 300.0}):
            flows = opening_stationary.solve(
                {fixture.TOWN: {fixture.GRAIN: 1_000_000.0, fixture.METAL: 40.0}}, fixture.recipes(), prices, WAGES, RATE)
            self.assertAlmostEqual(flows.income, flows.final_value, places=6)

    def test_prices_that_equal_cost_leave_no_profit(self):
        prices = {fixture.GRAIN: 0.3, fixture.ORE: 0.048, fixture.METAL: 1000.0 * 0.048 + 45.0}
        flows = opening_stationary.solve(
            {fixture.TOWN: {fixture.GRAIN: 1_000_000.0, fixture.METAL: 40.0}}, fixture.recipes(), prices, WAGES, RATE)
        self.assertAlmostEqual(flows.profit, 0.0, places=6)


class LabourBalanceTests(unittest.TestCase):
    def test_hours_offered_over_hours_hired(self):
        hours = {fixture.LABOURER: 600_000.0}
        self.assertAlmostEqual(opening_stationary.hours_offered_over_demanded(hours, 6_600_000.0, fixture.LABOURER), 11.0)
        self.assertIsNone(opening_stationary.hours_offered_over_demanded(hours, 100.0, fixture.SMITH))

    def test_the_survival_wage_spreads_the_floors_of_a_workers_people_over_his_hours(self):
        self.assertAlmostEqual(opening_stationary.survival_wage_per_hour(75.0, 2.0, 2000.0), 0.075)

    def test_hours_that_clear_leave_the_stated_slack(self):
        self.assertAlmostEqual(opening_stationary.hours_that_clear_at(600_000.0, 4000.0, 0.1), 165.0)


if __name__ == "__main__":
    unittest.main()
