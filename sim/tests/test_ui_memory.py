"""The UI's own memory (sim/ui/memory.py) lives in the save's `interface` slot. Complaint 640: the slot's rules are called on
a stand-in game; the slot in the save is test_interface_slot_in_save."""
QUICK_TOPIC = True

import os
import tempfile
import types
import unittest

from sim.ui import memory


def _game(interface=None):
    return types.SimpleNamespace(state=types.SimpleNamespace(interface={} if interface is None else interface))


class RememberedTests(unittest.TestCase):

    def test_a_topic_starts_empty_and_is_kept_in_the_interface_slot(self):
        game = _game()
        self.assertEqual(memory.remembered(game, "notes"), {})
        memory.remembered(game, "notes")["1"] = {"year": 100}
        self.assertEqual(game.state.interface, {"notes": {"1": {"year": 100}}})

    def test_asking_again_returns_the_same_dict(self):
        game = _game()
        self.assertIs(memory.remembered(game, "notes"), memory.remembered(game, "notes"))

    def test_two_topics_do_not_share_a_dict(self):
        game = _game()
        memory.remembered(game, "notes")["a"] = 1
        self.assertEqual(memory.remembered(game, "goals"), {})

    def test_two_games_never_share_one_memory(self):
        first, second = _game(), _game()
        memory.remembered(first, "notes")["1"] = {"text": "only here"}
        self.assertEqual(memory.remembered(second, "notes"), {})


class SnapshotTests(unittest.TestCase):

    def test_a_snapshot_is_a_copy_that_later_writes_do_not_change(self):
        game = _game()
        memory.remembered(game, "notes")["1"] = {"text": "first"}
        taken = memory.snapshot(game)
        memory.remembered(game, "notes")["1"]["text"] = "changed"
        self.assertEqual(taken["notes"]["1"]["text"], "first")

    def test_restore_puts_a_copy_in_the_slot_and_forgets_what_was_there(self):
        game = _game({"old": {"x": 1}})
        saved = {"notes": {"1": {"text": "kept"}}}
        memory.restore(game, saved)
        self.assertEqual(game.state.interface, saved)
        game.state.interface["notes"]["1"]["text"] = "edited"
        self.assertEqual(saved["notes"]["1"]["text"], "kept")

    def test_restoring_nothing_leaves_an_empty_memory(self):
        game = _game({"old": {"x": 1}})
        memory.restore(game, None)
        self.assertEqual(game.state.interface, {})


class SidecarTests(unittest.TestCase):

    def test_merging_into_the_sidecar_keeps_what_another_writer_put_there(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "game.json")
            memory.merge_session_meta(path, {"other_writer": "kept"})
            memory.merge_session_meta(path, {"checkpoint": True})
            meta = memory.settings.load_session_meta(path)
        self.assertEqual((meta.get("other_writer"), meta.get("checkpoint")), ("kept", True))


if __name__ == "__main__":
    unittest.main()
