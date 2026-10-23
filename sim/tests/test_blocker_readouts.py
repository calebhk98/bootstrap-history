"""Complaints/125, 263: the refusal of a start is the first blocker's text, so the refusal and every readout that lists
blockers are one function. StartingMixin.start_refusal on a stand-in game."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.projects_starting import StartingMixin


def game_with(blockers):
    return types.SimpleNamespace(start_blockers=lambda node_id, extra_owed=0.0: blockers)


class StartRefusal(unittest.TestCase):

    def test_the_refusal_is_the_first_blockers_text(self):
        game = game_with([{"kind": "supply", "text": "first"}, {"kind": "money", "text": "second"}])
        self.assertEqual(StartingMixin.start_refusal(game, "node"), "first")

    def test_a_node_with_no_blockers_has_no_refusal(self):
        self.assertIsNone(StartingMixin.start_refusal(game_with([]), "node"))


if __name__ == "__main__":
    unittest.main()
