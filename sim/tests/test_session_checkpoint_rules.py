"""A manual save is a frozen checkpoint and the Endless horizon is a large finite one. Rules: `settings.is_checkpoint`
(the milestone filename, or the sidecar marker), `_pick_milestone_filename` (distinct names), `_play_resolve_session` (a
resumed checkpoint is never autosaved over: the sitting forks a new session file), the horizon question's Endless
choice, and `_is_endless_horizon`. Streams are stubs; no game is built."""
QUICK_TOPIC = True

import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.engine import settings
from sim.ui import cli, cli_interactive, cli_interactive_saveload


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def test_a_milestone_by_its_filename_is_a_checkpoint(self):
        self.assertTrue(settings.is_checkpoint(os.path.join(self.folder, "rome_100ad_saved_3.json")))

    def test_an_ordinary_session_file_is_not(self):
        self.assertFalse(settings.is_checkpoint(os.path.join(self.folder, "rome_100ad.json")))
        self.assertFalse(settings.is_checkpoint(None))

    def test_a_renamed_save_is_still_a_checkpoint_by_its_sidecar_marker(self):
        path = os.path.join(self.folder, "my_favourite_moment.json")
        with open(path + ".meta.json", "w") as sidecar:
            json.dump({"checkpoint": True}, sidecar)
        self.assertTrue(settings.is_checkpoint(path))

    def test_milestones_saved_together_get_distinct_names_in_the_save_directory(self):
        with mock.patch.dict(os.environ, {settings.SAVE_DIR_ENV: self.folder}):
            first = cli_interactive_saveload._pick_milestone_filename("rome_100ad")
            second = cli_interactive_saveload._pick_milestone_filename("rome_100ad")
        self.assertNotEqual(first, second)
        self.assertEqual(os.path.dirname(first), self.folder)

    def test_the_horizon_is_read_from_the_saves_sidecar(self):
        path = os.path.join(self.folder, "game.json")
        with open(path + ".meta.json", "w") as sidecar:
            json.dump({"horizon_years": cli.ENDLESS_HORIZON_YEARS}, sidecar)
        self.assertEqual(settings.load_session_meta(path)["horizon_years"], cli.ENDLESS_HORIZON_YEARS)


class ResumeTests(unittest.TestCase):
    """`_play_resolve_session` on a save that exists: the engine's load and save are stubs that record the path."""

    def resume(self, path):
        sim = SimpleNamespace(civ={"id": "rome_100ad"}, year=-100, nodes={})
        loaded, saved = [], []
        with mock.patch.object(cli_interactive, "load_state", lambda game, session: loaded.append(session)), \
                mock.patch.object(cli_interactive, "save_session", lambda game, session: saved.append(session)), \
                mock.patch.object(cli_interactive, "_pick_session_filename", lambda civ_id: "/forked/%s.json" % civ_id), \
                mock.patch.object(cli_interactive, "_carry_known_routes", lambda *arguments: None), \
                mock.patch.object(cli_interactive, "_is_claimed_slot", lambda session: False), \
                mock.patch("builtins.print"):
            result = cli_interactive._play_resolve_session(SimpleNamespace(civ=None), sim, path)
        return result, loaded, saved

    def make_save(self, name):
        path = os.path.join(tempfile.mkdtemp(), name)
        open(path, "w").close()
        return path

    def test_an_ordinary_save_goes_on_autosaving_to_itself(self):
        path = self.make_save("rome_100ad.json")
        (session, fresh), loaded, saved = self.resume(path)
        self.assertEqual((session, fresh, loaded, saved), (path, False, [path], []))

    def test_a_checkpoint_is_read_but_the_sitting_autosaves_to_a_new_file_written_at_once(self):
        path = self.make_save("rome_100ad_saved_1.json")
        (session, fresh), loaded, saved = self.resume(path)
        self.assertEqual(loaded, [path])
        self.assertNotEqual(session, path)
        self.assertEqual(saved, [session])
        self.assertFalse(fresh)


class EndlessTests(unittest.TestCase):
    def ask(self, answers):
        with mock.patch("builtins.input", side_effect=answers), mock.patch("builtins.print"):
            return cli_interactive._new_game_ask_horizon({"default_horizon": 500})

    def test_choosing_endless_by_number_carries_the_large_finite_horizon(self):
        number = 1 + [mode[0] for mode in cli.HORIZON_MODES].index("endless")
        self.assertEqual(self.ask([str(number)]), cli.ENDLESS_HORIZON_YEARS)

    def test_choosing_endless_by_name_does_the_same(self):
        self.assertEqual(self.ask(["endless"]), cli.ENDLESS_HORIZON_YEARS)

    def test_a_named_preset_carries_its_years(self):
        self.assertEqual(self.ask(["challenge"]), 400)

    def test_a_remembered_endless_horizon_is_accepted_by_a_blank_answer(self):
        with mock.patch("builtins.input", side_effect=[""]), mock.patch("builtins.print"):
            self.assertEqual(cli_interactive._new_game_ask_horizon({"default_horizon": cli.ENDLESS_HORIZON_YEARS}),
                             cli.ENDLESS_HORIZON_YEARS)

    def test_a_game_with_the_endless_span_is_endless_and_one_with_a_standard_span_is_not(self):
        self.assertTrue(cli._is_endless_horizon(-100 + cli.ENDLESS_HORIZON_YEARS, -100))
        self.assertFalse(cli._is_endless_horizon(-100 + 500, -100))


if __name__ == "__main__":
    unittest.main()
