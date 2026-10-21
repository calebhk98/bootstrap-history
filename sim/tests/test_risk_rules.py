"""Complaint 640: the multipliers on a node's bare risk (`risk_rules`, `industry_depth.depth_risk_multiplier`) on built inputs."""

QUICK_TOPIC = True

import unittest

from sim.engine.industry_depth import RISK_SHARE_AT_FULL_DEPTH, depth_risk_multiplier
from sim.engine.risk_rules import control_relief_multiplier, effective_risk_of

FACTOR = 0.65


class DepthLearning(unittest.TestCase):
    def test_an_industry_with_no_depth_leaves_the_bare_risk(self):
        self.assertEqual(depth_risk_multiplier(0.0), 1.0)

    def test_each_step_of_depth_lowers_the_risk_and_full_depth_stops_at_the_floor_share(self):
        shares = [depth_risk_multiplier(depth / 4.0) for depth in range(5)]
        self.assertTrue(all(later < earlier for earlier, later in zip(shares, shares[1:])), shares)
        self.assertAlmostEqual(shares[-1], RISK_SHARE_AT_FULL_DEPTH)
        self.assertGreater(shares[-1], 0.0)


class ControlRelief(unittest.TestCase):
    def test_no_controller_in_force_leaves_the_risk(self):
        self.assertEqual(control_relief_multiplier("process_control", [], FACTOR), 1.0)

    def test_a_controller_for_the_nodes_failure_kind_cuts_the_risk_by_the_factor(self):
        self.assertEqual(control_relief_multiplier("process_control", ["process_control"], FACTOR), FACTOR)

    def test_a_controller_for_another_kind_gives_no_relief(self):
        self.assertEqual(control_relief_multiplier("mechanical", ["process_control"], FACTOR), 1.0)

    def test_two_controllers_of_one_kind_relieve_once_not_twice(self):
        self.assertEqual(control_relief_multiplier("process_control", ["process_control", "process_control"], FACTOR), FACTOR)


class EffectiveRisk(unittest.TestCase):
    def test_with_every_multiplier_at_one_it_is_the_bare_risk(self):
        self.assertEqual(effective_risk_of(0.45, 1.0, 1.0, 1.0), 0.45)

    def test_the_multipliers_compound_rather_than_override(self):
        depth = depth_risk_multiplier(1.0)
        self.assertAlmostEqual(effective_risk_of(0.45, depth, FACTOR, 0.8), 0.45 * depth * FACTOR * 0.8)
        self.assertLess(effective_risk_of(0.45, depth, FACTOR, 1.0), effective_risk_of(0.45, depth, 1.0, 1.0))

    def test_learning_and_relief_together_never_reach_zero(self):
        self.assertGreater(effective_risk_of(0.45, depth_risk_multiplier(1.0), FACTOR, 1.0), 0.0)
        self.assertGreaterEqual(effective_risk_of(0.45, depth_risk_multiplier(1.0), FACTOR, 1.0),
                                0.45 * RISK_SHARE_AT_FULL_DEPTH * FACTOR - 1e-12)

    def test_a_node_with_no_risk_stays_without_any(self):
        self.assertEqual(effective_risk_of(0.0, 0.5, FACTOR, 0.8), 0.0)


if __name__ == "__main__":
    unittest.main()
