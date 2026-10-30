"""Finished nodes are summed in the tree's order, whatever strategy order the game was started with, so the
opening economy (and the shipped openings keyed on it) do not depend on the strategy or goal."""
QUICK_TOPIC = True

import unittest

from sim.production.api import caches

TREE = {"fire": {}, "loom": {}, "coin": {}, "steam": {}}


class DoneInTreeOrderTests(unittest.TestCase):
    def test_the_order_is_the_trees_whatever_the_set_iterates_in(self):
        for done in ({"coin", "fire", "loom"}, {"loom", "coin", "fire"}, {"fire", "loom", "coin"}):
            self.assertEqual(caches.in_tree_order(TREE, done), ["fire", "loom", "coin"])

    def test_the_order_is_kept_until_the_done_set_changes(self):
        memos = caches.SeatMemos()
        first = memos.done_in_order(TREE, {"coin", "fire"})
        self.assertIs(memos.done_in_order(TREE, {"coin", "fire", "loom"}), first)
        memos.capability_factor = 1.0
        memos.forget_done()
        self.assertIsNone(memos.capability_factor)
        self.assertEqual(memos.done_in_order(TREE, {"coin", "fire", "loom"}), ["fire", "loom", "coin"])


if __name__ == "__main__":
    unittest.main()
