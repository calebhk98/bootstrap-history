"""Complaint 47: the disease burden reaches the population step. `Sim._disease_burden` hands the technologies' weights and the
holdings to `burden_from_holdings` (stand-in `self`), and `step_regions` hands the burden it is given to every region's step."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.engine import core
from sim.engine.core import Sim
from sim.world import regional_population
from sim.world.demography import Population


class DiseaseBurdenReadsTheHoldings(unittest.TestCase):
    def test_the_weights_are_the_effects_population_figures_and_the_holdings_are_the_games(self):
        recorded = []
        game = SimpleNamespace(DISEASE_BURDEN_TECH_IDS=("water", "vaccine"),
                               _tech_effects={"water": {"population": 0.05}, "vaccine": {}},
                               disease_burden_held=lambda tech_id: 1.0 if tech_id == "water" else 0.0)
        with mock.patch.object(core, "burden_from_holdings", lambda weights, held: recorded.append((weights, held)) or 0.4):
            burden = Sim._disease_burden(game)
        self.assertEqual(burden, 0.4)
        self.assertEqual(recorded, [({"water": 0.05, "vaccine": 0.0}, {"water": 1.0, "vaccine": 0.0})])


class StepRegionsPassesTheBurden(unittest.TestCase):
    def test_every_region_steps_under_the_burden_it_was_given(self):
        seen = []

        class Region:
            children = working_age = elderly = 1.0

            def step(self, kcal, **keywords):
                seen.append(keywords["disease_burden"])
                return None
        regional_population.step_regions({"a": Region(), "b": Region()}, {"a": 1.0, "b": 1.0}, 0.3, {}, None, {}, {})
        self.assertEqual(seen, [0.3, 0.3])

    def test_a_cleaner_society_loses_fewer_people_to_the_same_food(self):
        def deaths(burden):
            regions = {"a": Population.stationary(100000.0)}
            food = {"a": regional_population.kcal_per_day_fed(regions["a"], 1.0)}
            return regional_population.step_regions(regions, food, burden, {}, None, {}, {})["a"].deaths
        self.assertLess(deaths(0.0), deaths(1.0))


if __name__ == "__main__":
    unittest.main()
