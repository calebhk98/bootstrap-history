"""Scenario: a provider's deaths reach the population step in a real game. The provider door is test_externalities; the
yield factor reaching land-bound producers is test_externality_pooled_harvest."""

import unittest

from sim.engine import externalities
from sim.tests import harness


def a_year(provider=None):
    externalities.clear()
    if provider is not None:
        externalities.register(provider)
    game = harness.unopened_sim("england_1300")
    game._demographic_recovery(game.state.scenario.year)
    return game


class ExternalitiesInAGameTests(unittest.TestCase):
    def tearDown(self):
        externalities.clear()

    def test_provided_deaths_are_deaths_in_the_demographic_step(self):
        baseline = a_year()._last_demographic_step
        harmed = a_year(lambda sim, year: {"deaths_by_band": {"working_age": 1000.0}})._last_demographic_step
        self.assertAlmostEqual(harmed.deaths_working_age - baseline.deaths_working_age, 1000.0, places=3)
        self.assertEqual(harmed.deaths_children, baseline.deaths_children)


if __name__ == "__main__":
    unittest.main()
