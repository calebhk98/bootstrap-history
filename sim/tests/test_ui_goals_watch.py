"""ui_goals_watch: the in-game goals view and watched goals (Complaint 268). Complaint 640: the rules are called on a
stand-in game holding a small tree; the save round trip and the `commitments` wiring of a played game are in
test_commitments_report_wiring and test_interface_slot_in_save."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.tests.ui_stand_in import StandIn
from sim.ui.proto import goals_watch
from sim.ui.proto.render_typed import render_pretty
from sim.ui.proto.typed import parse_typed

CATALOG = [{"node": "steam", "name": "Steam engine"}, {"node": "radio", "name": "Radio"},
           {"node": "genes", "name": "Genetics"}, {"node": "formal", "name": "The formal goal"}]


def _game(fog=False, visible=("steam", "radio", "formal"), goal="formal", goal_year=None, done=()):
    nodes = {"base": {"name": "Base", "pre": []},
             "steam": {"name": "Steam engine", "pre": ["base"]},
             "radio": {"name": "Radio", "pre": ["steam"]},
             "genes": {"name": "Genetics", "pre": ["base"]},
             "formal": {"name": "The formal goal", "pre": ["steam", "radio"]}}
    game = StandIn(tree_nodes=nodes, goal=lambda: {"node": game.goal, "year": game.goal_year}, fog_of_war=lambda: game.fog,
                   techniques_held=lambda: game.done, visibility=lambda node_id, memo=None: game.is_visible(node_id))
    game.goal, game.goal_year, game.fog, game.done = goal, goal_year, fog, set(done)
    game.state = types.SimpleNamespace(interface={})
    game.is_visible = lambda node_id: node_id in visible
    return game


def _in(game, function, *arguments):
    with mock.patch.object(goals_watch, "_catalog", lambda sim: [goal for goal in CATALOG if goal["node"] in sim.view("tree_nodes")()]):
        return function(game, *arguments)


class GoalsReportTests(unittest.TestCase):

    def test_the_view_shows_progress_toward_the_formal_goal_counting_its_prerequisites(self):
        report = _in(_game(done={"base"}), goals_watch.goals_report)
        self.assertEqual(report["formal"]["id"], "formal")
        self.assertEqual((report["formal"]["done"], report["formal"]["total"]), (1, 4))

    def test_a_goal_can_be_watched_by_name_and_the_formal_goal_is_untouched(self):
        game = _game()
        reply = _in(game, goals_watch.watch, "Steam engine")
        self.assertEqual([row["id"] for row in reply["watched"]], ["steam"])
        self.assertEqual(game.goal, "formal")

    def test_a_watched_goal_leaves_the_choices(self):
        reply = _in(_game(), goals_watch.watch, "steam")
        self.assertTrue(all(row["id"] != "steam" for row in reply["choices"]))

    def test_the_formal_goal_cannot_be_watched(self):
        self.assertFalse(_in(_game(), goals_watch.watch, "formal")["ok"])

    def test_an_unknown_goal_is_refused(self):
        self.assertFalse(_in(_game(), goals_watch.watch, "no such goal at all")["ok"])

    def test_a_goal_can_be_unwatched(self):
        game = _game()
        _in(game, goals_watch.watch, "radio")
        self.assertEqual(_in(game, goals_watch.unwatch, "radio")["watched"], [])

    def test_a_goal_not_watched_cannot_be_unwatched(self):
        self.assertFalse(_in(_game(), goals_watch.unwatch, "radio")["ok"])

    def test_watching_twice_lists_the_goal_once(self):
        game = _game()
        _in(game, goals_watch.watch, "radio")
        reply = _in(game, goals_watch.watch, "radio")
        self.assertEqual([row["id"] for row in reply["watched"]], ["radio"])

    def test_only_so_many_goals_can_be_watched(self):
        game = _game()
        game.state.interface["goals_watch"] = {"ids": ["g%d" % number for number in range(goals_watch.MAX_WATCHED)]}
        self.assertFalse(_in(game, goals_watch.watch, "radio")["ok"])

    def test_promote_needs_the_formal_goal_reached_and_then_makes_a_watched_goal_formal(self):
        game = _game()
        _in(game, goals_watch.watch, "radio")
        self.assertFalse(_in(game, goals_watch.promote, "radio")["ok"])
        game.goal_year = 100
        with mock.patch.object(goals_watch.ui_port, "set_goal", lambda sim, node_id: setattr(sim, "goal", node_id)):
            reply = _in(game, goals_watch.promote, "radio")
        self.assertTrue(reply.get("ok") is not False)
        self.assertEqual(game.goal, "radio")
        self.assertEqual(reply["watched"], [])


class FogTests(unittest.TestCase):
    """A goal the player cannot know is never named and cannot be watched."""

    def test_under_fog_hidden_goals_are_only_counted_and_the_choices_are_all_in_view(self):
        game = _game(fog=True, visible=("steam", "radio"))
        report = _in(game, goals_watch.goals_report)
        self.assertEqual(report["unknown_goals"], 1)
        self.assertTrue(all(game.is_visible(row["id"]) for row in report["choices"]))

    def test_under_fog_a_formal_goal_out_of_view_is_a_count_with_no_name(self):
        report = _in(_game(fog=True, visible=("steam",)), goals_watch.goals_report)
        self.assertIsNone(report["formal"]["id"])
        self.assertIsNone(report["formal"]["name"])
        self.assertGreater(report["formal"]["total"], 0)

    def test_a_fogged_goals_name_cannot_be_watched_and_the_refusal_does_not_confirm_it(self):
        refusal = _in(_game(fog=True, visible=("steam",)), goals_watch.watch, "Genetics")
        self.assertFalse(refusal["ok"])
        self.assertNotIn("Genetics", refusal["error"].replace("%r" % "Genetics", ""))

    def test_a_watched_goal_that_fog_hides_is_listed_without_its_name(self):
        game = _game(fog=True, visible=("steam",))
        game.state.interface["goals_watch"] = {"ids": ["genes"]}
        row = goals_watch.watched_rows(game)[0]
        self.assertEqual((row["id"], row["name"]), (None, None))


class TypedAndScreenTests(unittest.TestCase):

    def test_typed_goals_watch_carries_the_goal_words(self):
        self.assertEqual(parse_typed("goals watch Steam engine")[0],
                         {"cmd": "goals", "action": "watch", "goal": "Steam engine"})

    def test_bare_goals_stays_bare(self):
        self.assertEqual(parse_typed("goals")[0], {"cmd": "goals"})

    def test_a_fogged_goal_shows_only_counts(self):
        formal = {"id": None, "name": None, "done": 4, "total": 40, "reached": False, "year_reached": None}
        hidden = {"id": None, "name": None, "done": 1, "total": 9, "reached": False}
        text = render_pretty("goals", {"ok": True, "formal": formal, "watched": [hidden], "choices": [],
                                       "unknown_goals": 3, "fog": True, "note": "n"})
        # presentation: counts are shown as "N of M" and unknown goals as "N more"
        for word in ("4 of 40", "1 of 9", "3 more"):
            self.assertIn(word, text)


if __name__ == "__main__":
    unittest.main()
