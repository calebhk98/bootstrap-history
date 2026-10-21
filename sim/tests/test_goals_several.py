"""Goals keyed by id with a reach year each, the anatomy hook and goal-cache invalidation (Complaint 422)."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine.core_properties import ForwardingPropertiesMixin
from sim.engine.fog import FogMixin
from sim.engine.goals import GoalsMixin
from sim.ui.proto import anatomy

# a chain a <- b <- c, and a separate goal d needing only e
NODES = {"a": {"pre": []}, "b": {"pre": ["a"]}, "c": {"pre": ["b"]}, "d": {"pre": ["e"]}, "e": {"pre": []}}


class StubGame(GoalsMixin):
    """The real goal bookkeeping and the real `goal` property over a plain state."""
    goal = ForwardingPropertiesMixin.goal
    on_road_to_goal = FogMixin.on_road_to_goal

    def __init__(self, goal):
        self.nodes = NODES
        self.civ = {}
        self.WIN_CONDITION_ANATOMY = {}
        self.state = SimpleNamespace(_goal=None, seat_progress=SimpleNamespace(goal_years={}, goal_year=None))
        self.goal = goal

    def _win_condition_value(self, condition):
        return 0.25


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


class GoalYears(unittest.TestCase):

    def test_the_formal_goal_records_its_year_when_reached(self):
        game = StubGame("c")
        game.record_goal_reached("c", 1000)
        self.assertEqual(game.state.seat_progress.goal_years, {"c": 1000})
        self.assertEqual(game.state.seat_progress.goal_year, 1000)

    def test_a_node_that_is_not_the_goal_records_nothing(self):
        game = StubGame("c")
        game.record_goal_reached("a", 1000)
        self.assertEqual(game.state.seat_progress.goal_years, {})
        self.assertIsNone(game.state.seat_progress.goal_year)

    def test_a_new_goal_starts_with_no_year_and_each_goal_keeps_its_own(self):
        game = StubGame("c")
        game.record_goal_reached("c", 1000)
        game.set_goal("d")
        self.assertIsNone(game.state.seat_progress.goal_year)
        game.record_goal_reached("d", 1007)
        self.assertEqual(game.state.seat_progress.goal_years, {"c": 1000, "d": 1007})
        self.assertEqual(game.state.seat_progress.goal_year, 1007)

    def test_returning_to_a_reached_goal_restores_its_year(self):
        game = StubGame("c")
        game.record_goal_reached("c", 1000)
        game.set_goal("d")
        game.set_goal("c")
        self.assertEqual(game.state.seat_progress.goal_year, 1000)

    def test_a_year_already_recorded_is_never_overwritten(self):
        game = StubGame("c")
        game.record_goal_reached("c", 1000)
        game.record_goal_reached("c", 1050)
        self.assertEqual(game.state.seat_progress.goal_years["c"], 1000)


class AnatomyHook(unittest.TestCase):

    def test_the_hook_returns_label_value_unit_rows_with_the_live_metric(self):
        rows = StubGame("c").win_condition_anatomy({"metric": "literacy_general", "op": ">=", "value": 0.2})
        self.assertTrue(rows and all(len(row) == 3 for row in rows))
        self.assertIn(("current", 0.25, "fraction"), rows)

    def test_a_mod_registers_its_own_anatomy(self):
        game = StubGame("c")
        game.WIN_CONDITION_ANATOMY["mod_metric"] = lambda sim_, condition: [("grain stock", 3.0, "tonnes")]
        self.assertEqual(game.win_condition_anatomy({"metric": "mod_metric"}), [("grain stock", 3.0, "tonnes")])

    def test_the_anatomy_command_uses_the_hook_for_a_metric_it_has_no_rule_for(self):
        game = StubGame("c")
        game.WIN_CONDITION_ANATOMY["mod_metric"] = lambda sim_, condition: [("grain stock", 3.0, "tonnes")]
        reply = anatomy.anatomy_for(game, {"metric": "mod_metric", "op": ">=", "value": 1.0})
        self.assertFalse(reply["generic"])
        # presentation: the label of an anatomy row
        self.assertEqual(reply["rows"][0]["label"], "grain stock")


if __name__ == "__main__":
    unittest.main()
