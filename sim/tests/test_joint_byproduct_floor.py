"""Complaints/309: a joint by-product with no demand keeps a positive floor price and never underflows."""

QUICK_TOPIC = True

import unittest

from sim.engine import joint_allocation
from sim.engine import prices as price_engine
from sim.engine.data import load_civ


class JointByproductFloorTests(unittest.TestCase):

    def test_by_product_in_a_glut_keeps_a_floor_and_the_batch_is_still_recovered(self):
        outputs = {"tar_kg": 1000.0, "charcoal_kg": 2500.0}
        prices = joint_allocation.allocate_joint_cost(
            outputs, {}, 760.0, {"tar_kg": 1e-9, "charcoal_kg": 4.0})
        standalone_per_kg = 760.0 / 3500.0
        self.assertGreaterEqual(
            prices["tar_kg"], joint_allocation.JOINT_BYPRODUCT_FLOOR_SHARE * standalone_per_kg)
        recovered = sum(prices[name] * quantity for name, quantity in outputs.items())
        self.assertAlmostEqual(recovered, 760.0)

    def test_a_floor_does_not_lift_an_output_already_above_it(self):
        outputs = {"main_kg": 1000.0, "gem_kg": 1.0}
        prices = joint_allocation.allocate_joint_cost(outputs, {}, 100.0, {"gem_kg": 500.0})
        self.assertGreater(prices["gem_kg"], 100.0 * prices["main_kg"])

    def test_solved_wood_tar_is_not_a_denormal(self):
        from sim import simulator
        _tree, prices_json, _nodes, _wages, _goods = simulator.load()
        civ = load_civ("rome_100ad")
        solved = price_engine.solved_prices(
            frozenset(civ["starting_techs"]), prices_json, civilization_id="rome_100ad",
            interest_rate=float(civ["starting_interest_rate"]))
        self.assertGreater(solved.prices_in_labour_hours["wood_tar_kg"], 1e-4)


if __name__ == "__main__":
    unittest.main()
