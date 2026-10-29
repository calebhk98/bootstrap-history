"""Complaint 800: nodes of an unstartable route that tie on how much is missing are listed by id, whatever order `road` was
handed in (a set's order changes with the hash seed). `route_blockers` is called on a stand-in sim."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.ui.proto import route_blockers as module


def stand_in():
    views = {"techniques_held": lambda: set(), "start_blockers": lambda node_id: [], "start_check": lambda node_id: (False, "why " + node_id)}
    return SimpleNamespace(view=views.__getitem__)


class RouteBlockers(unittest.TestCase):
    def listed(self, road, count=3):
        closures = {"a": {"x"}, "b": {"x"}, "c": {"x"}, "d": {"x", "y"}, "near": set()}
        with mock.patch.object(module, "closure", lambda nodes, node_id: closures[node_id]):
            return [row["id"] for row in module.route_blockers(stand_in(), {}, road, count)]

    def test_nodes_that_tie_are_listed_by_id_whatever_order_the_road_comes_in(self):
        self.assertEqual(self.listed(["d", "c", "b", "a", "near"]), ["near", "a", "b"])
        self.assertEqual(self.listed(["near", "b", "d", "a", "c"]), ["near", "a", "b"])
        self.assertEqual(self.listed({"c", "a", "b", "d", "near"}), ["near", "a", "b"])
