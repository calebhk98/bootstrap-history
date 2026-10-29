"""What the seats module works out of a seat's goal (the road to it, its length in years) is dropped when the goal changes
(Complaint 422); the goal years are test_seats_module's. Each test calls one handler or view on a written-out slot."""

QUICK_TOPIC = True

import unittest

from sim.knowledge.api import closure
from sim.seats.api import ForgetGoalClosure, RememberGoalFloor, SetGoal
from sim.seats.module import Seats
from sim.seats.state import SeatsSeat
from sim.tests import module_harness

# a chain a <- b <- c, and a separate goal d needing only e
NODES = {"a": {"pre": []}, "b": {"pre": ["a"]}, "c": {"pre": ["b"]}, "d": {"pre": ["e"]}, "e": {"pre": []}}


def seats_with_goal(goal, acting="founder"):
    module = module_harness.build(Seats, seat=SeatsSeat(goal=goal), views={"tree_closure": lambda goal: closure(NODES, goal)})
    module.clock.act_as(acting)
    return module


def on_the_road(module):
    return {node for node in NODES if module.on_road_to_goal(node)}


class GoalCaches(unittest.TestCase):

    def test_the_goal_road_is_the_closure_of_the_goal(self):
        self.assertEqual(on_the_road(seats_with_goal("c")), {"a", "b", "c"})

    def test_changing_the_goal_drops_the_cached_road(self):
        module = seats_with_goal("c")
        on_the_road(module)
        module.set_goal(SetGoal("d"))
        self.assertEqual(on_the_road(module), {"d", "e"})

    def test_the_critical_floor_is_none_until_it_is_remembered_and_then_the_value_set(self):
        module = seats_with_goal("c")
        self.assertIsNone(module.goal_critical_floor())
        module.remember_goal_floor(RememberGoalFloor(123.0))
        self.assertEqual(module.goal_critical_floor(), 123.0)

    def test_changing_the_goal_drops_the_cached_critical_floor(self):
        module = seats_with_goal("c")
        module.remember_goal_floor(RememberGoalFloor(123.0))
        module.set_goal(SetGoal("d"))
        self.assertIsNone(module.goal_critical_floor())

    def test_forgetting_the_goal_closure_drops_the_critical_floor_too(self):
        module = seats_with_goal("c")
        module.remember_goal_floor(RememberGoalFloor(123.0))
        module.forget_goal_closure(ForgetGoalClosure())
        self.assertIsNone(module.goal_critical_floor())

    def test_the_critical_floor_is_the_acting_seats_own(self):
        module = seats_with_goal("c", acting="founder")
        module.remember_goal_floor(RememberGoalFloor(123.0))
        module.clock.act_as("second")
        self.assertIsNone(module.goal_critical_floor())

    def test_the_goal_road_is_the_acting_seats_own(self):
        module = seats_with_goal("c", acting="founder")
        self.assertEqual(on_the_road(module), {"a", "b", "c"})
        module.clock.act_as("second")
        self.assertIsNone(module.goal_closure())

    def test_the_second_seats_road_is_worked_out_from_its_own_goal(self):
        module = seats_with_goal("c", acting="founder")
        on_the_road(module)
        module.clock.act_as("second")
        module.set_goal(SetGoal("d"))
        self.assertEqual(on_the_road(module), {"d", "e"})
        module.clock.act_as("founder")
        self.assertEqual(on_the_road(module), {"a", "b", "c"})


if __name__ == "__main__":
    unittest.main()
