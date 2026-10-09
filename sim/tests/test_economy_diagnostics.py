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

    def test_decomposition_gives_the_three_shares_of_labour_and_margins(self):
        setup = economy_fixture.small_setup()
        _economy, outcomes = economy_fixture.run(setup, years=6)
        figures = diagnostics.summary(outcomes, setup, economy_fixture.GRAIN, [economy_fixture.METAL])
        for key in ("hired_share", "wage_over_floor", "staple_over_labour", "unskilled_wage", "wage_floor"):
            self.assertIn(key, figures)
        self.assertGreaterEqual(outcomes[-1].wage_floor_per_hour, 0.0)

    def test_summary_of_a_fixture_run(self):
        setup = economy_fixture.small_setup()
        _economy, outcomes = economy_fixture.run(setup, years=6)
        figures = diagnostics.summary(outcomes, setup, economy_fixture.GRAIN, [economy_fixture.METAL])
        self.assertTrue(0.0 < figures["hired_share"] <= 1.0)
        self.assertTrue(0.0 <= figures["hunger_share"] <= 1.0)
        self.assertGreater(figures["staple_over_labour"], 0.0)


if __name__ == "__main__":
    unittest.main()
