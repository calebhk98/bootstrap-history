"""A hazard with a `condition` is resolved against what the household has, and the player is told which way it went, once
(the hazards module's resolve_hazard_condition, over the techniques held and the notices already told)."""
QUICK_TOPIC = True

import unittest

from sim.reporting.api import RecordEvent
from sim.tests import hazards_host, module_harness


def module_holding(known):
    return hazards_host.build(techniques_held=set(known))


def told(module):
    return [command for command in module_harness.sent(module) if isinstance(command, RecordEvent)]


def crossing():
    return {"name": "The crossings", "output_factor": 0.6, "sack_chance": 0.3, "staff_loss": 0.2,
            "condition": {"field": "output_factor", "requires_all": ["rotation", "land"], "outcome": "avert",
                          "met_message": "you feed yourself", "unmet_message": "the grain fleet fails"}}


def resolve(module, year=406, start=406):
    return module.resolve_hazard_condition(crossing(), year, start)


class TellingTheCondition(unittest.TestCase):
    def test_a_condition_not_met_fires_as_written_and_says_so_with_its_cause(self):
        module = module_holding({"rotation"})
        result = resolve(module)
        self.assertEqual(result["output_factor"], 0.6)
        self.assertEqual([event.kind for event in told(module)], ["hazard_condition_unmet"])
        self.assertEqual(told(module)[0].facts["hazard"], "The crossings")

    def test_a_condition_met_averts_the_field_and_says_so_with_its_cause(self):
        module = module_holding({"rotation", "land"})
        result = resolve(module)
        self.assertNotIn("output_factor", result)
        self.assertIn("sack_chance", result)
        self.assertIn("staff_loss", result)
        self.assertEqual([event.kind for event in told(module)], ["hazard_condition_met"])

    def test_the_hazard_is_told_once_however_often_its_window_is_resolved(self):
        module = module_holding({"rotation", "land"})
        resolve(module)
        resolve(module)
        self.assertEqual(len(told(module)), 1)

    def test_a_year_inside_the_window_but_not_its_first_says_nothing(self):
        module = module_holding(set())
        resolve(module, year=407, start=406)
        self.assertEqual(told(module), [])

    def test_a_hazard_with_no_condition_is_returned_untouched_and_unannounced(self):
        module = module_holding(set())
        plain = {"name": "plain", "output_factor": 0.5}
        self.assertIs(module.resolve_hazard_condition(plain, 406, 406), plain)
        self.assertEqual(told(module), [])


if __name__ == "__main__":
    unittest.main()
