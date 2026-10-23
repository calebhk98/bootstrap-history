"""delay_kinds and delay_phrase: running projects grouped by the kind of delay each waits on, as the multi-year
step warning names it. Projects are given as the `waiting_on` sentence `state` builds for each."""

QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.ui.proto import guidance


def kinds_of(waiting_by_project):
    rows = {node_id: {"waiting_on": waiting} for node_id, waiting in waiting_by_project.items()}
    with mock.patch.object(guidance, "_agent_state_active_projects", lambda sim, nodes: rows):
        return guidance.delay_kinds(None, {})


class DelayKinds(unittest.TestCase):

    def test_projects_waiting_only_on_their_calendar_floor_are_one_calendar_group(self):
        kinds = kinds_of({"b": "the calendar floor", "a": "the calendar floor"})
        self.assertEqual(kinds, {"calendar": ["a", "b"]})
        self.assertEqual(guidance.delay_phrase(kinds), "calendar (2)")

    def test_money_and_calendar_projects_are_separate_groups(self):
        kinds = kinds_of({"a": "the calendar floor", "b": "money for the next stage"})
        self.assertEqual(sorted(kinds), ["calendar", "money"])

    def test_nothing_running_is_named_as_such(self):
        self.assertEqual(kinds_of({}), {})
        self.assertEqual(guidance.delay_phrase({}), "nothing running")


if __name__ == "__main__":
    unittest.main()
