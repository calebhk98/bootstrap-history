"""A save says what game it is. A fogged game refuses a save played without fog (`fog_mismatch`), and resuming
`play --session` needs no --civ while a contradicting --civ is refused (`_civ_for_session`). Each function is called once on
inputs written out here; the save file reads (`civ_of_save`, `_is_claimed_slot`) are replaced by recorders."""
import contextlib
import io
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.engine.save_fog import fog_mismatch
from sim.refusal import cause_of
from sim.ui import cli

QUICK_TOPIC = True


class FogMismatch(unittest.TestCase):

    def test_a_fogged_game_refuses_a_save_played_without_fog(self):
        self.assertEqual(cause_of(fog_mismatch(True, False)), "save_fog_mismatch")

    def test_a_game_without_fog_accepts_a_save_played_without_fog(self):
        self.assertIsNone(fog_mismatch(False, False))

    def test_a_game_without_fog_accepts_a_fogged_save(self):
        self.assertIsNone(fog_mismatch(False, True))

    def test_a_fogged_game_accepts_a_fogged_save(self):
        self.assertIsNone(fog_mismatch(True, True))

    def test_a_fogged_game_accepts_a_save_that_does_not_say(self):
        self.assertIsNone(fog_mismatch(True, None))


def civ_for(session, asked, saved="england_1300", claimed=False, exists=True):
    with mock.patch.object(cli, "civ_of_save", lambda path: saved), mock.patch.object(cli, "_is_claimed_slot", lambda path: claimed), \
            mock.patch.object(cli.os.path, "exists", lambda path: exists), mock.patch.object(cli, "default_civilisation_id", lambda: "default"):
        return cli._civ_for_session(SimpleNamespace(session=session, civ=asked))


class CivilisationOfASession(unittest.TestCase):

    def test_a_save_resumes_without_being_told_which_game_it_is(self):
        self.assertEqual(civ_for("save.json", None), "england_1300")

    def test_naming_the_saved_civilisation_is_fine(self):
        self.assertEqual(civ_for("save.json", "england_1300"), "england_1300")

    def test_a_contradicting_civilisation_is_refused_with_a_nonzero_exit(self):
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(io.StringIO()):
            civ_for("save.json", "rome_100ad")
        self.assertEqual(raised.exception.code, 1)

    def test_a_claimed_empty_slot_is_a_new_game_of_the_civilisation_asked_for(self):
        self.assertEqual(civ_for("claimed.json", "han_china_100ad", claimed=True), "han_china_100ad")

    def test_no_session_gives_the_civilisation_asked_for(self):
        self.assertEqual(civ_for(None, "mexica_1500"), "mexica_1500")

    def test_no_session_and_no_civilisation_gives_the_default(self):
        self.assertEqual(civ_for(None, None), "default")


if __name__ == "__main__":
    unittest.main()
