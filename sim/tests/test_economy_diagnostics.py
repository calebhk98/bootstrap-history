"""Run figures: volatility, hired share, hunger share and price over labour cost."""

QUICK_TOPIC = True

import math
import types
import unittest

from sim.economy import diagnostics
from sim.tests import economy_fixture


class DiagnosticsTests(unittest.TestCase):
    def test_volatility_of_a_steady_and_a_swinging_price(self):
        self.assertAlmostEqual(diagnostics.volatility([2.0, 2.0, 2.0]), 0.0)
        self.assertAlmostEqual(diagnostics.volatility([1.0, math.e, 1.0]), 1.0)
        self.assertTrue(math.isnan(diagnostics.volatility([1.0])))

    def test_labour_cost_is_the_cheapest_recipe(self):
        setup = economy_fixture.small_setup()
        wages = {economy_fixture.LABOURER: 2.0}
        cost = diagnostics.labour_cost_per_unit(setup, wages, economy_fixture.GRAIN)
        self.assertAlmostEqual(cost, 300.0 * 2.0 / 1000.0)
        self.assertIsNone(diagnostics.labour_cost_per_unit(setup, {}, economy_fixture.GRAIN))

    def test_wage_over_floor_reads_the_unskilled_wage_against_the_floor(self):
        setup = economy_fixture.small_setup()
        outcome = types.SimpleNamespace(wages={setup.unskilled_trade: 0.3}, wage_floor_per_hour=0.2)
        self.assertAlmostEqual(diagnostics.wage_over_floor(outcome, setup), 1.5)
        outcome.wage_floor_per_hour = 0.0          # a plot that feeds the household leaves no floor to compare with
        self.assertTrue(math.isnan(diagnostics.wage_over_floor(outcome, setup)))

    def test_summary_takes_medians_of_the_years_figures_and_the_mean_hunger_share(self):
        setup = economy_fixture.small_setup()
        grain, metal, labourer = economy_fixture.GRAIN, economy_fixture.METAL, economy_fixture.LABOURER

        def year(grain_price, wage, hunger):
            return types.SimpleNamespace(prices={grain: grain_price, metal: 90.0}, wages={labourer: wage},
                                         hired_hours=75.0, idle_hours=25.0, wage_floor_per_hour=0.5,
                                         hunger_by_tile={"farms": hunger})
        outcomes = [year(0.3, 1.0, 0.0), year(0.6, 2.0, 100.0), year(0.3, 3.0, 200.0)]
        figures = diagnostics.summary(outcomes, setup, grain, [metal])
        people = sum(setup.opening_population_by_tile.values())
        floor = people * 250.0
        self.assertAlmostEqual(figures["hired_share"], 0.75)
        self.assertAlmostEqual(figures["unskilled_wage"], 2.0)
        self.assertAlmostEqual(figures["wage_floor"], 0.5)
        self.assertAlmostEqual(figures["wage_over_floor"], 4.0)
        self.assertAlmostEqual(figures["hunger_share"], 100.0 / floor)
        self.assertAlmostEqual(figures["staple_volatility"], math.log(2.0))
        self.assertAlmostEqual(figures["metal_volatility"], 0.0)
        self.assertAlmostEqual(figures["staple_over_labour"], 1.0)


if __name__ == "__main__":
    unittest.main()
