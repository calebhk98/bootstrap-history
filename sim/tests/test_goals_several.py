"""Goal-cache invalidation when the goal changes (Complaint 422); the goal years are test_seats_module's."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine.core_properties import ForwardingPropertiesMixin
from sim.engine.data import closure
from sim.engine.forward_seats import ForwardSeatsMixin
from sim.seats.api import RememberGoalClosure
from sim.seats.module import Seats
from sim.seats.state import SeatsSeat
from sim.tests import module_harness

# a chain a <- b <- c, and a separate goal d needing only e
NODES = {"a": {"pre": []}, "b": {"pre": ["a"]}, "c": {"pre": ["b"]}, "d": {"pre": ["e"]}, "e": {"pre": []}}


class StubGame(ForwardSeatsMixin):
    """The real cache dropping and the real `goal` property over a plain state."""
    goal = ForwardingPropertiesMixin.goal

    def on_road_to_goal(self, node_id):
        """The seats module's answer, over the goal this game holds and the memo it keeps on itself."""
        module = module_harness.build(
            Seats, seat=SeatsSeat(), views={"goal_closure": lambda: getattr(self, "_goal_closure", None),
                                            "tree_closure": lambda goal: closure(NODES, goal)},
            answers={RememberGoalClosure: lambda command: setattr(self, "_goal_closure", command.nodes)})
        module.goal = lambda: {"node": self.goal}
        return module.on_road_to_goal(node_id)

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
