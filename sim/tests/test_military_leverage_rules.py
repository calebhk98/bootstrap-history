"""What the founder's military work is worth, called with figures built here (Complaint 640; from the first playtests):
the leverage saturates well short of the whole branch, a war costs an armed empire less, and military work gives no
relief against staff loss."""
QUICK_TOPIC = True

import unittest

from sim.engine.military_rules import leverage_of
from sim.hazards import constants
from sim.hazards.rules import war_relief
from sim.tests import hazards_host

SATURATES_AT = 25.0
CAP = constants.MILITARY_WAR_RELIEF_CAP


class ArmedFounder:
    """The hazards module for a founder with built military nodes: no node counters, no state weapons."""

    def __init__(self, military_nodes):
        self.module = hazards_host.build(military_leverage=leverage_of(military_nodes, SATURATES_AT))

    def hazard_relief(self, kind):
        return self.module.hazard_relief(kind)

    def hazard_relief_entries(self, kind):
        return self.module.hazard_relief_entries(kind)


class LeverageTests(unittest.TestCase):
    def test_a_founder_with_no_military_work_has_none(self):
        self.assertEqual(leverage_of(0, SATURATES_AT), 0.0)

    def test_the_first_node_matters_most(self):
        first = leverage_of(1, SATURATES_AT)
        self.assertGreater(first, 0.0)
        self.assertGreater(first, leverage_of(2, SATURATES_AT) - first)

    def test_it_rises_with_every_node_until_it_saturates_and_then_stays_at_one(self):
        self.assertLess(leverage_of(1, SATURATES_AT), leverage_of(10, SATURATES_AT))
        self.assertLess(leverage_of(10, SATURATES_AT), 1.0)
        self.assertEqual(leverage_of(25, SATURATES_AT), 1.0)
        self.assertEqual(leverage_of(400, SATURATES_AT), 1.0)

    def test_it_saturates_at_a_fifth_of_a_branch_of_a_hundred_so_the_branch_is_not_a_strategy_of_its_own(self):
        self.assertEqual(leverage_of(25, SATURATES_AT), 1.0)
        self.assertLess(leverage_of(24, SATURATES_AT), 1.0)


class WarReliefTests(unittest.TestCase):
    def test_no_leverage_takes_nothing_off_a_war(self):
        self.assertEqual(war_relief(0.0, CAP), (1.0, None))

    def test_full_leverage_takes_the_cap_off_and_never_all_of_it(self):
        multiplier, reason = war_relief(1.0, CAP)
        self.assertAlmostEqual(multiplier, 1.0 - CAP)
        self.assertGreater(multiplier, 0.0)
        self.assertIn("military strength 100%", reason)

    def test_more_leverage_takes_more_off(self):
        self.assertLess(war_relief(0.8, CAP)[0], war_relief(0.2, CAP)[0])

    def test_a_war_costs_an_armed_empire_less_and_the_relief_names_its_source(self):
        unarmed, armed = ArmedFounder(0), ArmedFounder(25)
        self.assertLess(armed.hazard_relief("output_factor")[0], unarmed.hazard_relief("output_factor")[0])
        self.assertTrue(any(entry["source"] == "own_military_strength"
                            for entry in armed.hazard_relief_entries("output_factor")))

    def test_military_work_gives_no_relief_against_staff_loss(self):
        self.assertEqual(ArmedFounder(25).hazard_relief("staff_loss")[0], 1.0)
        self.assertEqual(ArmedFounder(0).hazard_relief("staff_loss")[0], 1.0)


if __name__ == "__main__":
    unittest.main()
