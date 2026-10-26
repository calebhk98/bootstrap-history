"""Goal-cache invalidation when the goal changes (Complaint 422); the goal years are test_seats_module's."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine.core_properties import ForwardingPropertiesMixin
from sim.engine.fog import FogMixin
from sim.engine.forward_seats import ForwardSeatsMixin

# a chain a <- b <- c, and a separate goal d needing only e
NODES = {"a": {"pre": []}, "b": {"pre": ["a"]}, "c": {"pre": ["b"]}, "d": {"pre": ["e"]}, "e": {"pre": []}}


class StubGame(ForwardSeatsMixin):
    """The real cache dropping and the real `goal` property over a plain state."""
    goal = ForwardingPropertiesMixin.goal
    on_road_to_goal = FogMixin.on_road_to_goal

    def __init__(self, goal):
        self.nodes = NODES
        self.civ = {}
        self.state = SimpleNamespace(_goal=None)
        self.goal = goal


class GoalCaches(unittest.TestCase):

    def test_the_goal_road_is_the_closure_of_the_goal(self):
        game = StubGame("c")
        self.assertEqual({node for node in NODES if game.on_road_to_goal(node)}, {"a", "b", "c"})

    def test_changing_the_goal_drops_the_cached_road(self):
        game = StubGame("c")
        game.on_road_to_goal("a")
        game.goal = "d"
        self.assertEqual({node for node in NODES if game.on_road_to_goal(node)}, {"d", "e"})

    def test_changing_the_goal_drops_the_cached_critical_floor(self):
        game = StubGame("c")
        game._goal_critical_floor = 123.0
        game.goal = "d"
        self.assertIsNone(getattr(game, "_goal_critical_floor", None))


if __name__ == "__main__":
    unittest.main()
