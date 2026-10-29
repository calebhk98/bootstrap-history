"""Complaint 640: the credit warnings and the rule that lets a long step stop on them, one rule at a time: the warning
band (`near_limit`), the halt of work in hand (`halt_active_projects`) and the table that says which lines interrupt a
multi-year step (`stops_a_step`). How a household's log and projects show them is test_credit_warning_wiring."""

import types
import unittest

from sim.finance.affordability import NEAR_LIMIT_FROM, near_limit
from sim.projects.api import halt_active_projects
from sim.refusal import LogLine
from sim.ui.proto.event_kinds import stops_a_step

QUICK_TOPIC = True
LIMIT = 1000.0


class StopsAStep(unittest.TestCase):
    def test_the_credit_warnings_stop_a_step_and_an_informational_line_does_not(self):
        self.assertTrue(stops_a_step(LogLine("credit_exhausted", "x")))
        self.assertTrue(stops_a_step(LogLine("credit_near_limit", "x")))
        self.assertFalse(stops_a_step(LogLine("arrears_interest", "x")))
        self.assertFalse(stops_a_step("a line with no kind"))


class NearTheLimit(unittest.TestCase):
    def test_the_warning_is_given_on_entering_the_band_and_not_again_while_in_it(self):
        warn, said, used = near_limit(-0.8 * LIMIT, LIMIT, False)
        self.assertTrue(warn)
        self.assertTrue(said)
        self.assertAlmostEqual(used, 0.8)
        self.assertEqual(near_limit(-0.8 * LIMIT, LIMIT, said)[0], False)

    def test_no_warning_far_from_the_limit_or_past_it(self):
        below_band = -0.5 * NEAR_LIMIT_FROM * LIMIT
        self.assertEqual(near_limit(below_band, LIMIT, False)[:2], (False, False))
        self.assertEqual(near_limit(-1.2 * LIMIT, LIMIT, False)[0], False)

    def test_the_warning_is_given_again_after_the_household_recovers(self):
        _warn, said, _used = near_limit(-0.8 * LIMIT, LIMIT, False)
        _warn, said, _used = near_limit(0.0, LIMIT, said)
        self.assertFalse(said)
        self.assertTrue(near_limit(-0.8 * LIMIT, LIMIT, said)[0])

    def test_no_credit_line_gives_no_warning(self):
        self.assertEqual(near_limit(-10.0, 0.0, False), (False, False, 0.0))


class HaltedProjects(unittest.TestCase):
    def test_work_in_hand_stops_and_what_was_paid_stands_to_its_credit(self):
        projects = types.SimpleNamespace(active={"b": {"spent": 40.0}, "a": {"spent": 5.0}}, bountied={"a", "z"})
        halted, kept = halt_active_projects(projects)
        self.assertEqual(halted, ["a", "b"])
        self.assertEqual(kept, 45.0)
        self.assertEqual(projects.active, {})
        self.assertEqual(projects.paid_towards, {"a": 5.0, "b": 40.0})
        self.assertEqual(projects.bountied, {"z"})

    def test_payment_adds_to_what_was_already_credited(self):
        projects = types.SimpleNamespace(active={"a": {"spent": 5.0}}, bountied=set(), paid_towards={"a": 10.0})
        halt_active_projects(projects)
        self.assertEqual(projects.paid_towards["a"], 15.0)


if __name__ == "__main__":
    unittest.main()
