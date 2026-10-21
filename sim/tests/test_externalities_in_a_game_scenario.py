"""Scenario: a provider's deaths reach the population step and its yield factor reaches land-bound producers in a real game.
The provider door is test_externalities; the yield arithmetic is test_economy_crop_yields."""

import unittest

from sim.engine import externalities
from sim.tests import harness


def a_year(provider=None):
    externalities.clear()
    if provider is not None:
        externalities.register(provider)
    game = harness.sim("england_1300")
    game.step()
    return game


class ExternalitiesInAGameTests(unittest.TestCase):
    def tearDown(self):
        externalities.clear()

    def test_provided_deaths_are_deaths_in_the_demographic_step(self):
        baseline = a_year()._last_demographic_step
        harmed = a_year(lambda sim, year: {"deaths_by_band": {"working_age": 1000.0}})._last_demographic_step
        self.assertAlmostEqual(harmed.deaths_working_age - baseline.deaths_working_age, 1000.0, places=3)
        self.assertEqual(harmed.deaths_children, baseline.deaths_children)

    def test_a_yield_factor_scales_the_land_producers_of_that_tile(self):
        game = a_year()
        agent = game.economy.agent
        from sim.economy import api as economy_api
        land_per_run = agent.economy().setup.land_per_run
        producers = {producer_id: producer for producer_id, producer in economy_api.producers_of(agent.economy()).items()
                     if land_per_run.get(producer.recipe_id, 0.0) > 0.0}
        tile = next(iter(producers.values())).tile
        before = agent._inputs({}).yield_factor_by_producer
        externalities.register(lambda sim, year: {"yield_factor_by_tile": {tile: 0.5}})
        after = agent._inputs({}).yield_factor_by_producer
        for producer_id, producer in producers.items():
            expected = before[producer_id] * (0.5 if producer.tile == tile else 1.0)
            self.assertAlmostEqual(after[producer_id], expected)


if __name__ == "__main__":
    unittest.main()
