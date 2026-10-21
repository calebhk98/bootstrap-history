"""Workforce advice sized to the real deficit, no closure warning for what an immortal founder guarantees, and
`allocate ... useful` capped at the useful work. Complaint 640: each rule is called on numbers built here; the checks in a
built game are in test_workforce_advice_and_allocate_cap_scenario."""
QUICK_TOPIC = True

import json
import unittest

from sim.engine.society_adoption import AdoptionMixin
from sim.engine.staffing_guarantee import closure_at_risk
from sim.ui.proto import typed
from sim.ui.proto.allocation_cap import capped_to_useful


def _hire_command(advice):
    return json.JSONDecoder().raw_decode(advice)[0]


class HireAdviceTests(unittest.TestCase):

    def test_the_scholar_advice_is_a_hire_command_sized_to_the_deficit(self):
        for deficit in (1, 2, 5):
            command = _hire_command(AdoptionMixin.staff_hire_advice(None, "scholars", deficit))
            self.assertEqual((command["cmd"], command["trade"], command["n"]), ("hire", "scholar", deficit))

    def test_with_no_known_deficit_the_advice_is_a_typical_order(self):
        self.assertGreater(_hire_command(AdoptionMixin.staff_hire_advice(None, "scholars"))["n"], 0)

    def test_the_craft_advice_is_sized_to_the_deficit_too(self):
        self.assertEqual(_hire_command(AdoptionMixin.staff_hire_advice(None, "artisans", 4))["n"], 4)


class ClosureWarningTests(unittest.TestCase):

    def test_no_warning_when_only_a_founder_who_cannot_leave_holds_the_work(self):
        # no hired people: the room is the founder's alone, so losing every hired person leaves it whole
        self.assertFalse(closure_at_risk(need=1.0, room=2.0, hired_held=0.0, founder_fixed=True))

    def test_a_mortal_founder_still_gets_the_warning(self):
        self.assertTrue(closure_at_risk(need=1.0, room=2.0, hired_held=0.0, founder_fixed=False))

    def test_hired_people_who_could_leave_put_the_concern_on_notice_even_with_an_immortal_founder(self):
        self.assertTrue(closure_at_risk(need=1.0, room=2.0, hired_held=3.0, founder_fixed=True))

    def test_a_concern_that_draws_nothing_from_the_pool_is_never_on_notice(self):
        self.assertFalse(closure_at_risk(need=0.0, room=-5.0, hired_held=3.0, founder_fixed=False))


class AllocateUsefulTests(unittest.TestCase):

    def test_useful_caps_the_order_at_what_the_project_can_use(self):
        self.assertEqual(capped_to_useful(540.0, 360.0, True), (360.0, 540.0))

    def test_an_order_within_the_useful_hours_is_taken_as_given(self):
        self.assertEqual(capped_to_useful(200.0, 360.0, True), (200.0, None))

    def test_without_useful_the_order_is_taken_as_given(self):
        self.assertEqual(capped_to_useful(540.0, 360.0, False), (540.0, None))

    def test_typed_words_reach_the_option(self):
        parsed, error = typed._parse_allocate("allocate", "x 540 useful", ["x", "useful"], [540.0], False)
        self.assertIsNone(error)
        self.assertTrue(parsed.get("useful"))


if __name__ == "__main__":
    unittest.main()
