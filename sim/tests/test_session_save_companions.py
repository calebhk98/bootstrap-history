"""Complaint 181: compressed saves, the version a save was written by, a readable summary and
rotating checkpoints beside a session save. Stubs stand in for the game, so no game is built."""
QUICK_TOPIC = True

import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.engine import save_companions, saveload
from sim.engine.state import SimulationState, HouseholdState, ProjectsState, ScenarioState, serialize_state, deserialize_state


def _stub_game(year):
    state = SimpleNamespace(_game_version="9.9.9", _seed="seedword")
    return SimpleNamespace(state=state, civ={"id": "rome_100ad"}, year=year, goal="goal_node",
                           capital=1234.4, done={"a", "b"})


def _fake_save_state(sim, path):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write('{"year": %s}' % sim.year)


class SaveCompanionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="save_companions_")
        self.path = os.path.join(self.directory, "game.json")
        patch = mock.patch.object(save_companions, "save_state", _fake_save_state)
        patch.start()
        self.addCleanup(patch.stop)

    def test_compressed_text_reads_back_and_plain_text_still_reads(self):
        for name in ("a.json", "b.json.gz"):
            path = os.path.join(self.directory, name)
            with open(path, "wb") as handle:
                handle.write(saveload._encode('{"x":1}', path))
            self.assertEqual(saveload.read_save_text(path), '{"x":1}')
        with open(os.path.join(self.directory, "b.json.gz"), "rb") as handle:
            self.assertEqual(handle.read(2), b"\x1f\x8b")
        self.assertEqual(saveload._encode("{}", "c.json"), b"{}")

    def test_the_version_is_in_the_serialised_state_and_not_checked_on_load(self):
        state = SimulationState(household=HouseholdState(capital=1), projects=ProjectsState(),
                                scenario=ScenarioState())
        state._game_version = "0.0.1-older"
        blob = serialize_state(state)
        self.assertEqual(blob["_game_version"], "0.0.1-older")
        self.assertEqual(deserialize_state(blob)._game_version, "0.0.1-older")

    def test_a_summary_is_written_and_names_the_version(self):
        save_companions.save_session(_stub_game(100), self.path)
        with open(self.path + save_companions.SUMMARY_SUFFIX, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("year: 100", text)
        self.assertIn("rome_100ad", text)
        self.assertIn("9.9.9", text)

    def test_an_unchanged_summary_is_not_rewritten(self):
        save_companions.save_session(_stub_game(100), self.path)
        summary = self.path + save_companions.SUMMARY_SUFFIX
        before = os.stat(summary).st_mtime_ns
        save_companions.save_session(_stub_game(100), self.path)
        self.assertEqual(os.stat(summary).st_mtime_ns, before)

    def test_one_checkpoint_per_year_and_only_the_newest_are_kept(self):
        for year in (100, 100, 101, 102, 103, 104):
            save_companions.save_session(_stub_game(year), self.path, kept=3)
        folder = save_companions.checkpoint_folder(self.path)
        self.assertEqual(sorted(os.listdir(folder)),
                         ["year_102.json", "year_103.json", "year_104.json"])
        with open(os.path.join(folder, "year_103.json"), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), '{"year": 103}')

    def test_a_compressed_session_gets_compressed_checkpoints(self):
        path = os.path.join(self.directory, "game.json.gz")
        save_companions.save_session(_stub_game(5), path)
        self.assertEqual(os.listdir(save_companions.checkpoint_folder(path)), ["year_5.json.gz"])

    def test_a_checkpoint_failure_does_not_lose_the_save(self):
        with mock.patch.object(save_companions.shutil, "copyfile", side_effect=OSError("disk full")):
            save_companions.save_session(_stub_game(7), self.path)
        self.assertTrue(os.path.exists(self.path))


if __name__ == "__main__":
    unittest.main()
