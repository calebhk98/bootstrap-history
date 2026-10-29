"""The rules behind the menu and the save browser, called directly: the rows `list_saves` reads from save files
(complaint 250), which files freeze (208), the protocol's save-path guard, the default goal the menu and `play` share
(259, 263), word seeds (254) and the `changes` window counting the arrival year (205)."""
QUICK_TOPIC = True

import json
import os
import tempfile
import unittest
from unittest import mock

from sim.engine import settings
from sim.engine.data import resolve_goal, selectable_goals
from sim.engine.saveload import goal_of_blob
from sim.engine.settings_table import normal_seed
from sim.ui.proto import economy as economy_commands
from sim.ui.proto import util as proto_util


def save_blob(year=100, capital=250.0, alive=True, goal="goal_node"):
    seat = {"goal": goal, "household": {"capital": capital}, "modules": {"seats": {"founder_alive": alive}}}
    return {"_civ": "rome_100ad", "acting_seat": "a", "seats": {"a": seat}, "modules": {"scenario": {"year": year}}}


class ListSaves(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def write(self, name, text):
        with open(os.path.join(self.directory, name), "w") as handle:
            handle.write(text)

    def rows(self):
        return {row["filename"]: row for row in settings.list_saves(self.directory)}

    def test_a_row_carries_the_year_capital_founder_status_and_goal_of_its_save(self):
        self.write("g.json", json.dumps(save_blob(year=137, capital=88.5, alive=False, goal="transistor")))
        row = self.rows()["g.json"]
        self.assertEqual((row["readable"], row["year"], row["capital"], row["founder_alive"], row["goal"]),
                         (True, 137, 88.5, False, "transistor"))

    def test_an_unparseable_file_is_listed_as_unreadable(self):
        self.write("broken.json", "{not json")
        self.assertIs(self.rows()["broken.json"]["readable"], False)

    def test_an_empty_slot_a_sidecar_and_a_json_that_is_no_save_are_not_listed(self):
        self.write("claimed.json", "")
        self.write("g.meta.json", "{}")
        self.write("other.json", json.dumps({"hello": 1}))
        self.assertEqual(self.rows(), {})

    def test_the_goal_of_a_save_is_the_acting_seats(self):
        self.assertEqual(goal_of_blob(save_blob(goal="transistor")), "transistor")
        self.assertIsNone(goal_of_blob({"seats": {}}))


class Checkpoints(unittest.TestCase):
    def test_a_milestone_file_name_is_a_frozen_checkpoint_and_an_ordinary_name_is_not(self):
        with mock.patch.object(settings, "load_session_meta", lambda path: {}):
            self.assertTrue(settings.is_checkpoint("/saves/rome_saved_3.json"))
            self.assertFalse(settings.is_checkpoint("/saves/rome.json"))
            self.assertFalse(settings.is_checkpoint(None))

    def test_a_sidecar_marking_a_checkpoint_freezes_a_renamed_file(self):
        with mock.patch.object(settings, "load_session_meta", lambda path: {"checkpoint": True}):
            self.assertTrue(settings.is_checkpoint("/saves/renamed.json"))


class SaveFileGuard(unittest.TestCase):
    def test_the_protocol_refuses_an_absolute_path_and_a_path_out_of_the_directory(self):
        self.assertIsNotNone(proto_util._unsafe_path("/tmp/exported.json"))
        self.assertIsNotNone(proto_util._unsafe_path("../exported.json"))
        self.assertIsNotNone(proto_util._unsafe_path("exported.txt"))
        self.assertIsNone(proto_util._unsafe_path("mygame.json"))

    def test_a_player_at_the_keyboard_may_save_to_an_absolute_path(self):
        with mock.patch.object(proto_util, "HUMAN_AT_KEYBOARD", True):
            self.assertIsNone(proto_util._unsafe_path("/tmp/exported.json"))


class DefaultGoal(unittest.TestCase):
    TREE = {"meta": {"goal_node": "transistor", "goals": [{"node": "steel"}, {"node": "transistor"}]}}
    NODES = {"steel": {"name": "Steel"}, "transistor": {"name": "Transistor"}}

    def test_the_menu_lists_first_the_goal_play_aims_at_without_a_goal_named(self):
        listed = [row["node"] for row in selectable_goals(self.TREE, self.NODES)]
        self.assertEqual(listed, ["transistor", "steel"])
        self.assertEqual(listed[0], resolve_goal(self.TREE, self.NODES, None))

    def test_a_default_goal_missing_from_the_catalogue_is_added_first(self):
        tree = {"meta": {"goal_node": "transistor", "goals": [{"node": "steel"}]}}
        self.assertEqual([row["node"] for row in selectable_goals(tree, self.NODES)], ["transistor", "steel"])


class WordSeeds(unittest.TestCase):
    def test_a_word_seed_is_kept_in_lower_case_and_a_number_stays_a_number(self):
        self.assertEqual(normal_seed(" Hello "), "hello")
        self.assertEqual(normal_seed("4242"), 4242)
        self.assertEqual(normal_seed(7), 7)
        self.assertNotEqual(normal_seed("hello"), normal_seed("goodbye"))


class ChangesWindow(unittest.TestCase):
    HISTORY = [{"year": 100}, {"year": 101}]

    def test_one_year_in_the_arrival_year_is_the_baseline(self):
        now, baseline, error = economy_commands._changes_baseline(self.HISTORY, 100, 101)
        self.assertIsNone(error)
        self.assertEqual((baseline["year"], now["year"]), (100, 101))

    def test_a_window_reaching_before_the_record_is_refused_with_the_years_available(self):
        _now, _baseline, error = economy_commands._changes_baseline(self.HISTORY, 99, 101)
        self.assertEqual(error["earliest_year"], 100)
        self.assertEqual(error["years_of_record"], 1)

    def test_no_record_is_refused(self):
        self.assertFalse(economy_commands._changes_baseline([], 0, 100)[2]["ok"])


if __name__ == "__main__":
    unittest.main()
