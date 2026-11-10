"""Small year readers of the labour side against the plain code they stand for: releasing many employers' bonded people at once,
the labour area names of the people-by-tile read, and the hours of every labour market from a plain list of results."""

QUICK_TOPIC = True

import copy
import random
import unittest

from sim.economy import bondage_hours
from sim.economy.labour_results_table import hours_by_market
from sim.economy.labour_state import PeopleByTile
from sim.economy.types import LabourResult
from sim.labour.market.market_state import MarketState


def random_held(rng):
    held = {}
    for tile in ("a", "b", "c"):
        for trade in ("smith", "miller"):
            by_employer = {"firm%d" % each: rng.uniform(0.0, 5.0) for each in range(5) if rng.random() < 0.5}
            if by_employer or rng.random() < 0.2:
                held.setdefault(tile, {})[trade] = by_employer
    return held


class ReleaseMany(unittest.TestCase):
    def test_releasing_a_set_is_releasing_each_in_turn(self):
        rng = random.Random(1)
        for _case in range(500):
            held = random_held(rng)
            leaving = rng.sample(["firm%d" % each for each in range(6)], rng.randint(0, 4))
            one_by_one, at_once = copy.deepcopy(held), copy.deepcopy(held)
            for employer in leaving:
                bondage_hours.release(one_by_one, employer)
            bondage_hours.release_many(at_once, leaving)
            self.assertEqual(at_once, one_by_one)
            self.assertEqual(list(at_once), list(one_by_one))


class PeopleByTileNames(unittest.TestCase):
    def test_tiles_are_the_areas_the_workers_view_names_in_name_order(self):
        state = MarketState(workers={"work@b": {"smith": [1.0, 2.0]}, "work@a": {"miller": [3.0]}}, trainees={"work@c": {}})
        found = PeopleByTile(state)
        self.assertEqual(list(found), [area.replace("work@", "") for area in sorted(state.workers)])
        self.assertEqual(found["a"], {"miller": 3.0})
        self.assertEqual(found["b"], {"smith": 3.0})


class HoursByMarket(unittest.TestCase):
    def test_a_plain_list_gives_hired_plus_idle_hours_by_market(self):
        results = [LabourResult("smith", "work@a", "denarius", 1.0, 10.0, 2.0, 3.0, ()), LabourResult("miller", "work@a", "denarius", 1.0, 4.0, 0.0, 1.5, ())]
        self.assertEqual(hours_by_market(results), {("smith", "work@a"): 13.0, ("miller", "work@a"): 5.5})


if __name__ == "__main__":
    unittest.main()
