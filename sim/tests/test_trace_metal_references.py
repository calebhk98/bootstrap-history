"""Trace metals are valued by a sole-output route or flagged as split by mass, and a zero-worth byproduct costs nothing."""

QUICK_TOPIC = True
import unittest
import warnings

from sim.engine import joint_allocation
from sim.tests.test_joint_allocation import solve_ungated


class ByproductAllocationTests(unittest.TestCase):
    outputs = {"main_kg": 1000.0, "waste_kg": 50.0}

    def test_a_free_byproduct_costs_nothing_and_leaves_the_batch_to_the_main_output(self):
        prices = joint_allocation.allocate_joint_cost(self.outputs, 100.0, {"waste_kg": 0.0})
        self.assertEqual(prices["waste_kg"], 0.0)
        self.assertAlmostEqual(prices["main_kg"] * 1000.0, 100.0)

    def test_a_byproduct_worth_more_than_its_mass_share_takes_more_than_its_mass_share(self):
        by_mass = joint_allocation.allocate_joint_cost(self.outputs, 100.0)
        valued = joint_allocation.allocate_joint_cost(self.outputs, 100.0, {"waste_kg": 40.0})
        self.assertGreater(valued["waste_kg"], by_mass["waste_kg"])


class TraceMetalRealDataTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cls.solved = solve_ungated()

    def test_platinum_costs_more_per_gram_than_nickel(self):
        prices = self.solved.prices
        self.assertGreater(prices["platinum_g"], prices["nickel_kg"] / 1000.0)

    def test_platinum_is_valued_by_its_own_route_and_not_split_by_mass(self):
        self.assertNotIn("platinum_g", self.solved.by_mass)

    def test_germanium_and_indium_are_flagged_with_a_warning(self):
        for material in ("germanium_g", "indium_g"):
            self.assertIn(material, self.solved.by_mass)
            self.assertTrue(
                any(material in message for message in self.solved.warnings),
                "no warning names %s" % material)


if __name__ == "__main__":
    unittest.main()
