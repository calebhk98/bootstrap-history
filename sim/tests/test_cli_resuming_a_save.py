"""`play` and `agent` leave a new game's economy unopened only when the sitting resumes a save that holds one."""
QUICK_TOPIC = True

import argparse
import os
import tempfile
import unittest

from sim.ui.cli_common import _resuming_a_save


class ResumingASaveTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def path(self, name, content=None):
        path = os.path.join(self.directory, name)
        if content is not None:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(content)
        return path

    def test_a_save_on_disk_is_resumed(self):
        self.assertTrue(_resuming_a_save(argparse.Namespace(session=self.path("game.json", "{}"))))

    def test_a_claimed_empty_slot_is_a_new_game(self):
        self.assertFalse(_resuming_a_save(argparse.Namespace(session=self.path("slot.json", ""))))

    def test_a_missing_file_is_a_new_game(self):
        self.assertFalse(_resuming_a_save(argparse.Namespace(session=self.path("missing.json"))))

    def test_no_session_is_a_new_game(self):
        self.assertFalse(_resuming_a_save(argparse.Namespace(session=None)))
        self.assertFalse(_resuming_a_save(argparse.Namespace()))


if __name__ == "__main__":
    unittest.main()
