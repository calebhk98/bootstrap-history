"""The engine bridge's application of the commands hazards sends to owners that have not moved: each does what the old hazard
code did inline, on a stand-in game that holds only what the write touches."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine import bridge_hazards
from sim.projects.api import ShutForgotten
from sim.projects.api import ResetProjectProgress
from sim.reporting.api import RecordEvent
from sim.tests import projects_host


class Writes(unittest.TestCase):
    def test_works_of_forgotten_techniques_are_no_longer_running_or_shut(self):
        projects = SimpleNamespace(operating={"a", "b", "c"}, mothballed={"a", "c"})
        game = SimpleNamespace(state=SimpleNamespace(projects=projects))
        bridge_hazards.shut_forgotten(game, ShutForgotten(("a", "b")))
        self.assertEqual((projects.operating, projects.mothballed), ({"c"}, {"c"}))

    def test_every_project_in_hand_goes_back_to_the_beginning(self):
        active = {"b": {"ph_left": 1.0, "yrs": 3.0}, "a": {"ph_left": 2.0, "yrs": 1.0}}
        module = projects_host.build(legacy_projects=SimpleNamespace(active=active), tree={"a": {"ph": 100.0}, "b": {"ph": 50.0}})
        module.apply_reset_project_progress(ResetProjectProgress())
        self.assertEqual(active, {"a": {"ph_left": 100.0, "yrs": 0.0}, "b": {"ph_left": 50.0, "yrs": 0.0}})


if __name__ == "__main__":
    unittest.main()
