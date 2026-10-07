"""The engine answers the strata's cost questions from the need-basket kernel on its own goods market."""
import unittest

from sim.engine.agents_port import SimWorld

from .harness import sim


class EngineFloorCostsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = SimWorld(sim(civ="rome_100ad", agent_economy=False))

    def test_every_floor_need_with_a_priced_good_has_a_positive_cost(self):
        costs = self.world.need_floor_costs_per_person_year()
        self.assertTrue(costs)
        self.assertTrue(all(cost > 0.0 for cost in costs.values()))

    def test_the_food_floor_is_the_subsistence_cost(self):
        self.assertEqual(self.world.subsistence_cost_per_person_year(),
                         self.world.need_floor_costs_per_person_year()["food"])

    def test_floors_the_climate_sets_reach_the_strata_costs(self):
        costs = self.world.need_floor_costs_per_person_year()
        self.assertGreater(len(costs), 1)


if __name__ == "__main__":
    unittest.main()
