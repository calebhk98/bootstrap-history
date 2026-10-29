"""Goal-cache invalidation when the goal changes (Complaint 422); the goal years are test_seats_module's."""

QUICK_TOPIC = True

import unittest

from sim.engine.core_properties import ForwardingPropertiesMixin
from sim.knowledge.api import closure
from sim.engine.bridge_seats import forget_goal_caches
from sim.seats.api import ForgetGoalCaches
from sim.seats.module import Seats
from sim.seats.state import SeatsSeat
from sim.tests import module_harness

# a chain a <- b <- c, and a separate goal d needing only e
NODES = {"a": {"pre": []}, "b": {"pre": ["a"]}, "c": {"pre": ["b"]}, "d": {"pre": ["e"]}, "e": {"pre": []}}


class StubGame:
    """The real `goal` property over the seats module; SetGoal goes to the module and the cache drop it sends to the engine's handler."""
    goal = ForwardingPropertiesMixin.goal

    def __init__(self, goal):
        self.module = module_harness.build(Seats, seat=SeatsSeat(), views={"tree_closure": lambda goal: closure(NODES, goal)})
        self.module.clock.act_as("founder")
        self.goal = goal

    def view(self, name):
        return getattr(self.module, name)

    def send(self, command):
        self.module.set_goal(command)
        for sent in self.module.needs.sent:
            if isinstance(sent, ForgetGoalCaches):
                forget_goal_caches(self, sent)
        self.module.needs.sent.clear()

    def on_road_to_goal(self, node_id):
        return self.module.on_road_to_goal(node_id)


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
