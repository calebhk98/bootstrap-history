"""Complaint 159: a --session path that does not exist and names no --civ is a typo, not a new game. The rule is called
with built arguments; nothing is built or written."""
QUICK_TOPIC = True

import os
import tempfile
import types
import unittest

from sim.ui import cli_interactive


class SessionTypoRule(unittest.TestCase):
    def test_a_missing_session_with_no_civ_refuses_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "newgame.json")
            result = cli_interactive._play_resolve_session(types.SimpleNamespace(civ=None), None, path)
            self.assertEqual(1, result)
            self.assertFalse(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
