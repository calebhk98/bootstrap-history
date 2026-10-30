"""Complaint 640 (the identity_cover persona): a persona makes the same strange work less alarming, and is not needed to build it.
`alarm_of` is asked of the polity module with the weights and the household's standing written out and the persona's effect as a
factor that is applied last; the persona's own declaration (an alarm factor under one, protection, no prerequisite on the work it
calms) is read from the tree."""
QUICK_TOPIC = True

import unittest

from sim.polity.constants import ALARM_PROTECTION_FLOOR, ALARM_WEIGHT_INEXPLICABLE
from sim.polity.state import PolitySeat
from sim.tests import polity_host
from sim.tests.harness import NODES

WEIGHTS = {"w_magic_fear": 1.0, "w_religious_rigidity": 1.0, "w_labour_saving": 0.0, "w_novelty": 0.0}


class Society:
    """The polity module with the weights and the household's standing written out and the persona's effect as a factor."""

    def __init__(self, protection=0.0, familiarity=0.0, persona_factor=1.0):
        self.module = polity_host.build(
            seat=PolitySeat(protection=protection, familiarity=familiarity), value_weights=WEIGHTS,
            effect_factor=lambda channel, start=1.0, exponent=None: start * persona_factor if channel == "alarm_factor" else start)

    def alarm_of(self, node):
        return self.module.alarm_of(node)


STRANGE = {"traits": ["inexplicable"]}


class AlarmOf(unittest.TestCase):
    def test_an_inexplicable_work_alarms_by_its_weight_times_the_societys_fear_of_magic(self):
        self.assertAlmostEqual(Society().alarm_of(STRANGE), ALARM_WEIGHT_INEXPLICABLE * WEIGHTS["w_magic_fear"])

    def test_a_work_with_no_alarming_trait_does_not_alarm(self):
        self.assertEqual(Society().alarm_of({"traits": ["commerce"]}), 0.0)

    def test_protection_lowers_the_alarm(self):
        self.assertAlmostEqual(Society(protection=0.4).alarm_of(STRANGE), Society().alarm_of(STRANGE) * 0.6)

    def test_protection_cannot_lower_it_below_its_floor(self):
        self.assertAlmostEqual(Society(protection=1.0).alarm_of(STRANGE), Society().alarm_of(STRANGE) * ALARM_PROTECTION_FLOOR)

    def test_a_persona_factor_lowers_the_same_work_further(self):
        self.assertAlmostEqual(Society(persona_factor=0.75).alarm_of(STRANGE), Society().alarm_of(STRANGE) * 0.75)


class PersonaDeclaration(unittest.TestCase):
    def test_the_persona_declares_an_alarm_factor_below_one_and_some_protection(self):
        mechanics = NODES["identity_cover"]["mechanics"]
        self.assertLess(mechanics["alarm_factor"]["factor"], 1.0)
        self.assertGreater(mechanics["protection"]["flat"], 0.0)

    def test_the_strange_work_it_calms_can_still_be_built_without_it(self):
        self.assertNotIn("identity_cover", NODES["hot_air_balloon"]["pre"])
        self.assertIn("inexplicable", NODES["hot_air_balloon"]["traits"])


if __name__ == "__main__":
    unittest.main()
