"""Complaint 47: the disease burden reaches the population step. The disease module's `disease_burden` hands the technologies' weights
and the holdings to `burden_from_holdings` (views answered by plain values), and `step_regions` hands the burden it is given to every region's step."""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.disease import burden
from sim.disease.module import Disease
from sim.tests import module_harness
from sim.world import regional_population
from sim.world.demography import Population

CLINICS = "clinics"


def burden_module(held, weights, coverage=(), coverage_share=lambda node_id: 0.0, mechanic_ids=None):
    """A disease module over technologies with these effect weights, holding `held`."""
    return module_harness.build(Disease, views={
        "mechanic": {"disease_burden": tuple(mechanic_ids or weights)}, "tech_effects": {tech: {"population": weight} if weight is not None else {}
                                                                                          for tech, weight in weights.items()},
        "techniques_held": set(held), "coverage": list(coverage), "coverage_share": coverage_share})


class DiseaseBurdenReadsTheHoldings(unittest.TestCase):
    def test_the_weights_are_the_effects_population_figures_and_the_holdings_are_the_games(self):
        recorded = []
        module = burden_module({"water"}, {"water": 0.05, "vaccine": None})
        with mock.patch.object(burden, "burden_from_holdings", lambda weights, held: recorded.append((weights, held)) or 0.4):
            result = module.disease_burden()
        self.assertEqual(result, 0.4)
        self.assertEqual(recorded, [({"water": 0.05, "vaccine": 0.0}, {"water": 1.0, "vaccine": 0.0})])

    def test_clinics_reaching_half_the_people_take_half_their_weight_off_the_burden(self):
        module = burden_module({CLINICS}, {"germ_theory": 1.0, CLINICS: 3.0}, coverage=[CLINICS], coverage_share=lambda node_id: 0.5)
        self.assertAlmostEqual(module.disease_burden(), 1.0 - 1.5 / 4.0, places=12)

    def test_clinics_built_but_shut_take_nothing_off(self):
        module = burden_module({CLINICS}, {"germ_theory": 1.0, CLINICS: 3.0}, coverage=[CLINICS], coverage_share=lambda node_id: 0.0)
        self.assertEqual(module.disease_burden(), 1.0)

    def test_every_technology_held_leaves_no_burden(self):
        module = burden_module({"germ_theory", CLINICS}, {"germ_theory": 1.0, CLINICS: 3.0})
        self.assertEqual(module.disease_burden(), 0.0)


class DiseaseBurdenHeldTests(unittest.TestCase):
    def test_a_work_that_declares_coverage_counts_as_the_share_it_serves(self):
        module = burden_module({CLINICS}, {CLINICS: 1.0}, coverage=[CLINICS], coverage_share=lambda node_id: 0.4)
        self.assertEqual(module.disease_burden_held(CLINICS), 0.4)

    def test_a_technology_that_declares_no_coverage_counts_whole_once_held(self):
        module = burden_module({CLINICS}, {CLINICS: 1.0})
        self.assertEqual(module.disease_burden_held(CLINICS), 1.0)

    def test_a_technology_not_held_counts_nothing(self):
        module = burden_module(set(), {"germ_theory": 1.0})
        self.assertEqual(module.disease_burden_held("germ_theory"), 0.0)


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
