"""Complaint 492: the royalty's base counts a seat's own workings like any owner's: tonnes by the tile of the deposit each
names (`rules.mined_tonnes_by_tile`) added to the firms' output by tile (`world_revenue.tonnes_on_tiles`). Plain values, no game."""
QUICK_TOPIC = True

import unittest

from sim.actors.world_revenue import tonnes_on_tiles
from sim.resources import rules


class FounderWorkingsPayTheRoyalty(unittest.TestCase):
    def test_workings_are_summed_on_the_tile_of_their_deposit(self):
        workings = [({"deposit": "a"}, 3.0), ({"deposit": "b"}, 2.0), ({"deposit": "a"}, 1.0), ({"deposit": None}, 9.0)]
        self.assertEqual(rules.mined_tonnes_by_tile(workings, {"a": "t1", "b": "t2"}), {"t1": 4.0, "t2": 2.0})

    def test_firms_and_workings_both_count_on_the_held_tiles_only(self):
        firms, workings = {"t1": 30.0, "t3": 7.0}, {"t1": 4.0, "t2": 2.0}
        self.assertAlmostEqual(tonnes_on_tiles([firms, workings], {"t1", "t2"}), 36.0)


if __name__ == "__main__":
    unittest.main()
