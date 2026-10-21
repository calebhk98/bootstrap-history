"""A defence credited to guns needs the powder works running (Complaints/245).

The rule is tested on fixtures in test_defence_stores.py (GunsNeedThePowderWorksRunning, TheMagazineRunsDry,
TheGarrisonMustBePresent, PowderIsAHeldMaterial); this file holds the shipped data's side of it.
"""
import unittest

from .harness import NODES

QUICK_TOPIC = True

ARTILLERY = "mil_artillery_piece"
POWDER = "gunpowder"
GUNS_LABEL = "guns on the walls"


class GunsOnWallsNeedPowder(unittest.TestCase):

    def test_artillery_counter_declares_the_powder_it_needs(self):
        counters = NODES[ARTILLERY]["mechanics"]["hazard_counters"]
        guns = [counter for counter in counters if counter["label"] == GUNS_LABEL]
        self.assertEqual(guns[0].get("requires_running"), [POWDER])

    def test_artillery_counter_declares_a_magazine_and_the_node_a_garrison(self):
        counters = NODES[ARTILLERY]["mechanics"]["hazard_counters"]
        guns = [counter for counter in counters if counter["label"] == GUNS_LABEL][0]
        self.assertTrue(guns.get("magazine"))
        self.assertTrue(NODES[ARTILLERY].get("garrison"))


if __name__ == "__main__":
    unittest.main()
