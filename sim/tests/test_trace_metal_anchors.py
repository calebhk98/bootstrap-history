"""Trace metals get a demand anchor or an explicit unanchored flag, and surplus byproducts price to disposal value."""
import unittest
import warnings

from sim import joint_allocation, solve_prices
from sim.tests.test_joint_allocation import solve_ungated
from sim.world import demand


class SurplusByproductAllocationTests(unittest.TestCase):
    outputs = {"main_kg": 1000.0, "waste_kg": 50.0}

    def test_a_satisfied_byproduct_prices_at_its_disposal_value(self):
        prices = joint_allocation.allocate_joint_cost(
            self.outputs, {}, 100.0, {"waste_kg": 0.1},
            disposal_value_by_material={"waste_kg": 0.5})
        self.assertAlmostEqual(prices["waste_kg"], 0.5)

    def test_the_other_outputs_still_recover_the_whole_batch(self):
        prices = joint_allocation.allocate_joint_cost(
            self.outputs, {}, 100.0, {"waste_kg": 0.1},
            disposal_value_by_material={"waste_kg": 0.5})
        recovered = sum(prices[name] * quantity for name, quantity in self.outputs.items())
        self.assertAlmostEqual(recovered, 100.0)
        self.assertAlmostEqual(prices["main_kg"] * 1000.0, 100.0 - 0.5 * 50.0)

    def test_a_byproduct_with_demand_above_disposal_value_is_not_treated_as_surplus(self):
        prices = joint_allocation.allocate_joint_cost(
            self.outputs, {}, 100.0, {"waste_kg": 40.0},
            disposal_value_by_material={"waste_kg": 0.5})
        self.assertGreater(prices["waste_kg"], 0.5)

    def test_a_free_byproduct_costs_nothing_and_leaves_the_batch_to_the_main_output(self):
        prices = joint_allocation.allocate_joint_cost(
            self.outputs, {}, 100.0, {"waste_kg": 0.0})
        self.assertEqual(prices["waste_kg"], 0.0)
        self.assertAlmostEqual(prices["main_kg"] * 1000.0, 100.0)

    def test_disposal_revenue_never_exceeds_the_batch_cost(self):
        prices = joint_allocation.allocate_joint_cost(
            self.outputs, {}, 10.0, {"waste_kg": 0.0},
            disposal_value_by_material={"waste_kg": 5.0})
        self.assertGreaterEqual(prices["main_kg"], 0.0)


class SolvedSurplusTests(unittest.TestCase):

    def test_a_solved_recipe_prices_its_surplus_output_at_the_recipe_disposal_value(self):
        entries = {"smelt": {
            "outputs": {"main_kg": 1000.0, "waste_kg": 50.0}, "inputs": {},
            "labour_hours": {"labourer": 100.0},
            "disposal_value_hours": {"waste_kg": 0.25}}}
        producers = solve_prices.build_producers_index(entries)

        class SatisfiedDemand:
            def prices(self, _prices):
                return {"waste_kg": 0.01}

        prices, _i, _r, _c = solve_prices.solve(
            entries, producers, {"main_kg", "waste_kg"}, {"labourer": 1.0},
            demand_anchors=SatisfiedDemand())
        self.assertAlmostEqual(prices["waste_kg"], 0.25, places=6)
        self.assertAlmostEqual(
            prices["main_kg"] * 1000.0 + prices["waste_kg"] * 50.0, 100.0, places=4)


class TraceMetalRealDataTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cls.unanchored_run = solve_ungated(False)
            cls.anchored_run = solve_ungated(True)

    def test_platinum_satisfies_a_need_and_has_a_supply_figure(self):
        anchors = joint_allocation.build_demand_anchors()
        self.assertIn("platinum_g", anchors.model.effectiveness["ornament"])
        self.assertIn("platinum_g", anchors.supply_by_material)

    def test_platinum_costs_more_per_gram_than_nickel(self):
        prices = self.anchored_run.prices
        self.assertGreater(prices["platinum_g"], prices["nickel_kg"] / 1000.0)

    def test_the_anchor_lifts_platinum_relative_to_nickel(self):
        before, after = self.unanchored_run.prices, self.anchored_run.prices
        self.assertGreater(after["platinum_g"] / after["nickel_kg"],
                           before["platinum_g"] / before["nickel_kg"])

    def test_germanium_and_indium_are_anchored_or_flagged_with_a_warning(self):
        anchors = joint_allocation.build_demand_anchors()
        run = solve_ungated(True)
        flagged = set(run.unanchored)
        for material in ("germanium_g", "indium_g"):
            if material in anchors.supply_by_material:
                continue
            self.assertIn(material, flagged)
            self.assertTrue(
                any(material in message for message in run.warnings),
                "no warning names %s" % material)


if __name__ == "__main__":
    unittest.main()
