"""`year_goods.with_floor_and_budget` builds the bid `dataclasses.replace` would, on random bids."""
QUICK_TOPIC = True

import dataclasses
import random
import unittest

from sim.economy.types import Bid
from sim.economy.year_goods import with_floor_and_budget


class WithFloorAndBudgetTests(unittest.TestCase):
    def test_equals_replace_on_random_bids(self):
        draw = random.Random(7)
        for _case in range(200):
            bid = Bid("h%d" % draw.randrange(5), "grain", "area", "tile", draw.uniform(0, 9), draw.uniform(0, 9),
                      draw.uniform(0.1, 3), draw.uniform(0, 2), draw.uniform(0, 50), draw.randrange(3),
                      draw.choice([float("inf"), draw.uniform(1, 5)]))
            floor, budget = draw.uniform(0, 9), draw.uniform(0, 50)
            made = with_floor_and_budget(bid, floor, budget)
            self.assertEqual(made, dataclasses.replace(bid, floor_quantity=floor, budget=budget))
            self.assertEqual(dataclasses.astuple(made), dataclasses.astuple(dataclasses.replace(bid, floor_quantity=floor, budget=budget)))


if __name__ == "__main__":
    unittest.main()
