"""The founder's crew is paid once: a derived upkeep is staff pay plus plant wear, and the staff's pay is already in
the payroll, so the share of a node's upkeep that is charged as upkeep is its plant part (`node_upkeep.non_labour_share`).
The charge the founder is made is in test_founder_income_rules.py."""
import unittest

from sim.production import node_upkeep

QUICK_TOPIC = True


class NonLabourShareTests(unittest.TestCase):

    def test_a_derived_upkeep_charges_its_plant_part_only(self):
        node = {"up": 100.0, "_upkeep_hours_parts": {"staff": 3.0, "plant": 1.0}}
        self.assertAlmostEqual(node_upkeep.non_labour_share(node), 0.25)

    def test_a_node_with_no_stated_crew_keeps_its_whole_upkeep(self):
        self.assertEqual(node_upkeep.non_labour_share({"up": 100.0}), 1.0)

    def test_a_staff_priced_node_charges_no_plant_upkeep(self):
        self.assertEqual(node_upkeep.non_labour_share({"up": 100.0, "_upkeep_basis": "staff"}), 0.0)

    def test_a_node_that_states_no_parts_at_all_keeps_the_whole(self):
        self.assertEqual(node_upkeep.non_labour_share({"up": 1.0, "_upkeep_hours_parts": {"staff": 0.0, "plant": 0.0}}), 1.0)


if __name__ == "__main__":
    unittest.main()
