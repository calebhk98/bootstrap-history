"""The commands hazards sends to the owners of the projects in hand and of the works running: each does what the old hazard code did
inline, on the module over a stand-in record that holds only what the write touches."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.projects.api import ResetProjectProgress
from sim.reporting.api import RecordEvent
from sim.tests import projects_host, ventures_host
from sim.ventures.api import ShutForgotten


class Writes(unittest.TestCase):
    def test_works_of_forgotten_techniques_are_no_longer_running_or_shut(self):
        module = ventures_host.build(operating={"b", "c", "a"}, projects_record=ventures_host.projects_record(mothballed={"x", "y"}))
        module.seat.business.mothball("a", 1, "by_choice")
        module.seat.business.mothball("z", 1, "by_choice")
        module.apply_shut_forgotten(ShutForgotten(("a", "b", "z")))
        self.assertEqual((module.operating(), module.mothballed()), ({"c"}, {"x", "y"}))

    def test_every_project_in_hand_goes_back_to_the_beginning(self):
        active = {"b": {"ph_left": 1.0, "yrs": 3.0}, "a": {"ph_left": 2.0, "yrs": 1.0}}
        module = projects_host.build(projects_record=SimpleNamespace(active=active), tree={"a": {"ph": 100.0}, "b": {"ph": 50.0}})
        module.apply_reset_project_progress(ResetProjectProgress())
        self.assertEqual(active, {"a": {"ph_left": 100.0, "yrs": 0.0}, "b": {"ph_left": 50.0, "yrs": 0.0}})


if __name__ == "__main__":
    unittest.main()
