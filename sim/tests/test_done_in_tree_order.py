"""Finished nodes are summed in the tree's order, whatever strategy order the game was started with, so the
opening economy (and the shipped openings keyed on it) do not depend on the strategy or goal."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.economy import EconomyMixin


def game(order):
    return types.SimpleNamespace(nodes={"fire": {}, "loom": {}, "coin": {}, "steam": {}}, order=list(order),
                                 household=types.SimpleNamespace(_done_seq=None),
                                 state=types.SimpleNamespace(projects=types.SimpleNamespace(done={"coin", "fire", "loom"})))


class DoneInTreeOrderTests(unittest.TestCase):
    def test_the_order_is_the_trees_whatever_the_strategy(self):
        for order in ([], ["coin", "loom"], ["loom", "steam", "coin", "fire"]):
            self.assertEqual(EconomyMixin.done_in_order(game(order)), ["fire", "loom", "coin"])


if __name__ == "__main__":
    unittest.main()
