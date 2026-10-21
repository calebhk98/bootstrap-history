"""Complaint 514 open question 6: a firm's crew is paid once, as wages through the labour market. A node's upkeep is
derived as its staff's pay plus plant wear, so the upkeep a firm pays is the non-labour part only
(`node_upkeep.non_labour_upkeep_money`). The year's charge in a running game is in test_firm_crew_paid_once_scenario.py."""
QUICK_TOPIC = True

import unittest

from sim.engine import node_upkeep

COST_SCALE = 1.5


class FirmUpkeepLeavesOutTheCrewsPay(unittest.TestCase):
    def test_the_quote_is_the_plant_part_of_the_upkeep(self):
        node = {"up": 100.0, "_upkeep_hours_parts": {"staff": 3.0, "plant": 1.0}}
        self.assertAlmostEqual(node_upkeep.non_labour_upkeep_money(100.0, node, 1.0, COST_SCALE), 100.0 * 0.25 * COST_SCALE)

    def test_the_quote_scales_with_the_firms_capacity(self):
        node = {"up": 100.0, "_upkeep_hours_parts": {"staff": 1.0, "plant": 1.0}}
        self.assertAlmostEqual(node_upkeep.non_labour_upkeep_money(100.0, node, 3.0, COST_SCALE),
                               3.0 * node_upkeep.non_labour_upkeep_money(100.0, node, 1.0, COST_SCALE))

    def test_a_node_whose_upkeep_has_no_stated_crew_keeps_its_whole_upkeep(self):
        self.assertAlmostEqual(node_upkeep.non_labour_upkeep_money(100.0, {"up": 100.0}, 1.0, COST_SCALE), 100.0 * COST_SCALE)


if __name__ == "__main__":
    unittest.main()
