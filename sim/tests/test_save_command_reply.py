"""Complaint 640: the `save` and `load` command's reply. A save or load of a file name answers ok with the year; a refused file
carries the refusal's `cause` and `facts` (never only prose); an unsafe or missing name is refused before any file is touched.
`_cmd_save` is called on a stand-in game with the engine's `save_state` and `load_state` replaced; which saves are refused is
test_save_refusal_rules."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.refusal import Refusal
from sim.ui.proto import dispatch
from sim.ui.proto.dispatch import _cmd_save
from sim.tests.ui_stand_in import Game

GAME = Game(year=120)


def ask(**fields):
    return _cmd_save(GAME, {}, dict(fields), None)


class SaveAndLoadReply(unittest.TestCase):
    def test_a_save_says_where_it_wrote_and_the_year(self):
        with mock.patch.object(dispatch, "save_state") as save:
            reply = ask(cmd="save", file="game.json")
        self.assertEqual(reply, {"ok": True, "saved": "game.json", "year": 120})
        save.assert_called_once_with(GAME, "game.json")

    def test_a_load_says_what_it_read_and_the_year(self):
        with mock.patch.object(dispatch, "load_state") as load:
            reply = ask(cmd="load", file="game.json")
        self.assertEqual(reply, {"ok": True, "loaded": "game.json", "year": 120})
        load.assert_called_once_with(GAME, "game.json")

    def test_a_refused_file_carries_the_refusals_cause_and_facts(self):
        refusal = Refusal("save_wrong_civilisation", "that save is for another civilisation", saved="norse", running="rome")
        with mock.patch.object(dispatch, "load_state", side_effect=ValueError(refusal)):
            reply = ask(cmd="load", file="norse.json")
        self.assertIs(reply["ok"], False)
        self.assertEqual(reply["cause"], "save_wrong_civilisation")
        self.assertEqual(reply["facts"], {"saved": "norse", "running": "rome"})

    def test_a_failure_with_no_cause_is_still_a_refusal_without_one(self):
        with mock.patch.object(dispatch, "load_state", side_effect=OSError("no such file")):
            reply = ask(cmd="load", file="missing.json")
        self.assertIs(reply["ok"], False)
        self.assertNotIn("cause", reply)

    def test_an_absolute_path_is_refused_and_no_file_is_touched(self):
        with mock.patch.object(dispatch, "save_state") as save:
            reply = ask(cmd="save", file="/etc/game.json")
        self.assertIs(reply["ok"], False)
        save.assert_not_called()

    def test_a_missing_file_name_is_refused(self):
        self.assertIs(ask(cmd="save")["ok"], False)


if __name__ == "__main__":
    unittest.main()
