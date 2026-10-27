"""Finished nodes are summed in the tree's order, whatever strategy order the game was started with, so the
opening economy (and the shipped openings keyed on it) do not depend on the strategy or goal."""
QUICK_TOPIC = True

import types
import unittest

from sim.production.api import caches

TREE = {"fire": {}, "loom": {}, "coin": {}, "steam": {}}


class DoneInTreeOrderTests(unittest.TestCase):
    def test_the_order_is_the_trees_whatever_the_set_iterates_in(self):
        for done in ({"coin", "fire", "loom"}, {"loom", "coin", "fire"}, {"fire", "loom", "coin"}):
            self.assertEqual(caches.in_tree_order(TREE, done), ["fire", "loom", "coin"])

    def test_the_order_is_kept_on_the_household_until_the_done_set_changes(self):
        household = types.SimpleNamespace(_done_seq=None, _cap_factor=1.0, bump_done_version=lambda: None)
        first = caches.done_in_order(household, TREE, {"coin", "fire"})
        self.assertIs(caches.done_in_order(household, TREE, {"coin", "fire", "loom"}), first)
        caches.forget_done(household)
        self.assertEqual(caches.done_in_order(household, TREE, {"coin", "fire", "loom"}), ["fire", "loom", "coin"])


if __name__ == "__main__":
    unittest.main()
