"""A durable that serves a need is seeded in households only where the society can have it, so its making entries state a gate."""

QUICK_TOPIC = True

import unittest

from sim.engine import validate_production


def maker(requires_node=None, output="ornament_metal_g"):
    entry = {"outputs": {output: 1.0}}
    if requires_node is not None:
        entry["requires_node"] = requires_node
    return entry


class NeedDurableGateTests(unittest.TestCase):
    def test_an_ungated_entry_making_a_need_serving_durable_is_a_problem(self):
        problems = validate_production.check_durable_gate({"ornament_metal": maker(None)}, {"ornament_metal_g"})
        self.assertEqual(len(problems), 1)

    def test_a_null_gate_is_a_problem(self):
        entry = maker()
        entry["requires_node"] = None
        self.assertEqual(len(validate_production.check_durable_gate({"ornament_metal": entry}, {"ornament_metal_g"})), 1)

    def test_a_gated_entry_is_fine(self):
        self.assertEqual(validate_production.check_durable_gate({"ornament_metal": maker("mat_metal")}, {"ornament_metal_g"}), [])

    def test_an_ungated_entry_making_something_else_is_fine(self):
        self.assertEqual(validate_production.check_durable_gate({"bread": maker(None, "bread_kg")}, {"ornament_metal_g"}), [])


if __name__ == "__main__":
    unittest.main()
