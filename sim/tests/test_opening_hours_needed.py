"""Numba port, the opening's labour demand: `opening_hours_needed.of_producers` (the kernel) gives the dicts the plain loop over
producers gave, the same numbers in the same order, on random recipes and producers; no game."""

QUICK_TOPIC = True

import random
import types
import unittest

from sim.economy import opening_hours_needed

TRADES = ["farmer", "smith", "miller", "carter", "weaver"]


def plain_loop(rows):
    """The loop the kernel replaced."""
    hours_needed = {}
    for recipe, area, sales in rows:
        needed = hours_needed.setdefault(area, {})
        for trade, hours in recipe.labour_hours.items():
            needed[trade] = needed.get(trade, 0.0) + sales * hours
    return hours_needed


def random_rows(rng):
    recipes = [types.SimpleNamespace(labour_hours={trade: rng.uniform(0.0, 30.0) for trade in rng.sample(TRADES, rng.randint(0, 4))})
               for _ in range(rng.randint(1, 8))]
    return [(rng.choice(recipes), "area%d" % rng.randint(0, 5), rng.uniform(0.0, 1000.0)) for _ in range(rng.randint(0, 60))]


class OpeningHoursNeededTest(unittest.TestCase):
    def test_same_dicts_in_the_same_order(self):
        rng = random.Random(7)
        for _case in range(200):
            rows = random_rows(rng)
            expected, got = plain_loop(rows), opening_hours_needed.of_producers(rows)
            self.assertEqual(list(expected), list(got))
            for area in expected:
                self.assertEqual(list(expected[area]), list(got[area]))
                for trade in expected[area]:
                    self.assertEqual(expected[area][trade], got[area][trade])      # same additions in the same order: same bits

    def test_no_producers(self):
        self.assertEqual({}, opening_hours_needed.of_producers([]))

    def test_a_recipe_of_no_labour_still_names_its_area(self):
        recipe = types.SimpleNamespace(labour_hours={})
        self.assertEqual({"a": {}}, opening_hours_needed.of_producers([(recipe, "a", 5.0)]))


if __name__ == "__main__":
    unittest.main()
