"""Complaints/309: a joint by-product with no demand is bounded by minus its disposal cost and never underflows."""

QUICK_TOPIC = True

import math
import unittest

from sim.engine import disposal_cost, joint_allocation
from sim.engine import prices as price_engine
from sim.engine.data import load_civ


class JointByproductFloorTests(unittest.TestCase):

    def test_by_product_in_a_glut_is_bounded_below_and_the_batch_is_still_recovered(self):
        outputs = {"tar_kg": 1000.0, "charcoal_kg": 2500.0}
        disposal = disposal_cost.disposal_cost_by_material(
            ["tar_kg"], {"waste_handling_job": 1.0, "waste_haulage_tkm": 0.3, "dump_ground_m2": 0.01})
        prices = joint_allocation.allocate_joint_cost(
            outputs, {}, 760.0, {"tar_kg": 1e-9, "charcoal_kg": 4.0},
            disposal_cost_by_material=disposal, glutted_materials={"tar_kg"})
        self.assertGreaterEqual(prices["tar_kg"], -disposal["tar_kg"] - 1e-12)
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
        tar_price = solved.prices_in_labour_hours["wood_tar_kg"]
        self.assertTrue(math.isfinite(tar_price))
        self.assertGreaterEqual(tar_price, -disposal_cost.disposal_cost_by_material(
            ["wood_tar_kg"], solved.prices_in_labour_hours, float(civ["starting_interest_rate"]))["wood_tar_kg"] - 1e-12)
        self.assertGreater(abs(tar_price), 1e-4)


if __name__ == "__main__":
    unittest.main()
