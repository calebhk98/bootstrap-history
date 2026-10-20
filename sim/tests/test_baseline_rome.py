"""Complaints 554 and 473: baseline checks on the Rome agent economy's hidden first stage run with fixed people and no
shocks (the run `simulator.py spin-up-trace` prints). Slow: the game build is about a minute and the 40-year trace
is cached on disk beside the money-supply test's (same years, so one run feeds both).

`test_the_price_level_wage_money_and_rate_settle` is THE settling test for Complaint 473 and FAILS on the current
code: the spin-up does not settle (the price level and wage drift for decades). Do not loosen it; it passes when
the spin-up reaches a resting economy. The bounds are declared in sim/economy/settling.py.
"""
import unittest

from sim.economy import api as economy_api
from sim.economy.baseline_checks import MIN_MONEY_REPLACEMENT, feasibility, money_replacement
from sim.economy.settling import SETTLING_WINDOW_YEARS, format_report, settling_report
from sim.engine.economy_port_setup import build_setup
from sim.engine.economy_port_year import YearInputs
from sim.tests import harness
from sim.tests.test_spin_up_money_supply import YEARS, cached_spin_up_trace

FEASIBILITY_YEARS = 4


class RomeBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = harness.sim()
        cls.rows = cached_spin_up_trace(cls.game, YEARS)

    def test_the_first_years_accounts_are_physically_feasible(self):
        setup = build_setup(self.game, self.game.state.economy.agent_economy["opening"])
        economy = economy_api.blank_economy(setup)
        economy_api.begin_spin_up(economy)
        inputs = YearInputs(year=0, population_by_tile={}, working_age_share=setup.working_share,
                            yield_factor_by_producer={}, engine_orders={})
        accounts = [economy.step(inputs).accounts for _year in range(FEASIBILITY_YEARS)]
        self.assertEqual(feasibility(accounts), [])

    def test_the_mint_replaces_the_coin_that_wears(self):
        replaced = money_replacement(self.rows, SETTLING_WINDOW_YEARS)
        self.assertGreaterEqual(replaced, MIN_MONEY_REPLACEMENT)

    def test_the_price_level_wage_money_and_rate_settle(self):
        report = settling_report(self.rows)
        unsettled = [item.name for item in report if not item.settled]
        self.assertEqual(unsettled, [], "not settled over the last %d of %d years:\n%s"
                         % (SETTLING_WINDOW_YEARS, YEARS, format_report(report)))


if __name__ == "__main__":
    unittest.main()
