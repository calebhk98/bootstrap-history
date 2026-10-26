"""Complaints/125, 263: the refusal of a start is the first blocker's text, so the refusal and every readout that lists
blockers are one function. The projects module's start_refusal over a given list of blockers."""
QUICK_TOPIC = True

import unittest

from sim.tests import projects_host


def game_with(blockers):
    return projects_host.build(start_blockers=lambda node_id, extra_owed=0.0: blockers)


class StartRefusal(unittest.TestCase):

    def test_the_refusal_is_the_first_blockers_text(self):
        game = game_with([{"kind": "supply", "text": "first"}, {"kind": "money", "text": "second"}])
        self.assertEqual(game.start_refusal("node"), "first")

    def test_a_node_with_no_blockers_has_no_refusal(self):
        self.assertIsNone(game_with([]).start_refusal("node"))


if __name__ == "__main__":
    unittest.main()
