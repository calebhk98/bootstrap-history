"""The project order the household's hours serve projects by: the rules that change it (sim/projects/order_rules.py), the module's three
commands over a plain world state, and the order's trip through the save's serialisation (Complaint 841). Each test calls one function."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.state import deserialize_state, serialize_state
from sim.projects import order_rules
from sim.projects.commands import PutProjectFirst, ReorderProjects, RestoreProjectOrder
from sim.projects.state import ProjectsWorld
from sim.tests import projects_host


class PutFirst(unittest.TestCase):
    def test_a_node_in_the_middle_moves_to_the_front(self):
        self.assertEqual(order_rules.put_first(["a", "b", "c"], "c"), ["c", "a", "b"])

    def test_a_node_the_order_lacks_is_added_at_the_front(self):
        self.assertEqual(order_rules.put_first(["a", "b"], "z"), ["z", "a", "b"])


class PlaceSequence(unittest.TestCase):
    def test_only_the_places_active_projects_hold_are_refilled(self):
        order = ["x", "a", "y", "b", "z"]
        self.assertEqual(order_rules.place_sequence(order, {"a", "b"}, ["b", "a"]), ["x", "b", "y", "a", "z"])

    def test_an_active_node_the_order_lacks_gets_a_place_at_the_end(self):
        self.assertEqual(order_rules.place_sequence(["x", "a"], {"a", "n"}, ["n", "a"]), ["x", "n", "a"])


class Commands(unittest.TestCase):
    def module(self, order):
        return projects_host.build(order=order, legacy_projects=types.SimpleNamespace(active={"b": {}, "c": {}}))

    def test_put_project_first_changes_the_published_order(self):
        module = self.module(["a", "b", "c"])
        module.apply_put_project_first(PutProjectFirst("c"))
        self.assertEqual(module.project_order(), ("c", "a", "b"))

    def test_reorder_projects_refills_the_active_places(self):
        module = self.module(["a", "b", "c"])
        module.apply_reorder_projects(ReorderProjects(("c", "b")))
        self.assertEqual(module.project_order(), ("a", "c", "b"))

    def test_restore_project_order_sets_the_whole_order(self):
        module = self.module(["a", "b", "c"])
        module.apply_restore_project_order(RestoreProjectOrder(("c", "b", "a")))
        self.assertEqual(module.project_order(), ("c", "b", "a"))


class SavedWithTheGame(unittest.TestCase):
    def test_the_order_survives_the_save_serialisation(self):
        saved = serialize_state(ProjectsWorld(order=["c", "a", "b"]))
        self.assertEqual(deserialize_state(saved, ProjectsWorld).order, ["c", "a", "b"])


if __name__ == "__main__":
    unittest.main()
