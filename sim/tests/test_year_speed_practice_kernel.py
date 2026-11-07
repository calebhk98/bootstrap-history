"""Complaint 497, numba port item 6: the practice kernels (the peers' mean practice per trade, the trades still
learning) give what the per-trade Python they replaced gave. Each is called beside a copy of the old code on random
crews; no game."""

QUICK_TOPIC = True

import math
import random
import types
import unittest

from sim.economy import entry_practice, households_basket, households_close, practice
from sim.economy.types import Recipe
from sim.world.need_basket import Basket, NeedSpec

# a kernel adds the peers left to right where the old code used math.fsum (exactly rounded), so the means differ in
# the last digits; a relative 1e-12 is far above that and far below any rule's effect
TOLERANCE = 1e-12


def old_pool_units(producers_of_recipe, trade):
    if not producers_of_recipe:
        return 1.0
    return practice.entrant_units([crew_runs.get(trade, practice.established_units()) for crew_runs in producers_of_recipe])


def old_entrant_crew_runs(recipe, peers):
    start = {trade: old_pool_units(peers, trade) for trade in sorted(recipe.labour_hours)}
    return {trade: units for trade, units in start.items() if practice.hours_multiplier(units) > 1.0}


def random_crews(rng, trades):
    return [{trade: rng.choice([rng.uniform(1.0, 3000.0), rng.uniform(1.0, 20.0)]) for trade in trades if rng.random() < 0.7}
            for _ in range(rng.randrange(0, 60))]


class PracticeKernelsAreTheOldRule(unittest.TestCase):

    def test_pool_units_matches_the_old_mean(self):
        rng = random.Random(11)
        for _round in range(60):
            crews = random_crews(rng, ("hand", "smith"))
            for trade in ("hand", "smith", "absent"):
                self.assertTrue(math.isclose(practice.pool_units(crews, trade), old_pool_units(crews, trade),
                                             rel_tol=TOLERANCE))

    def test_entrant_crew_runs_matches_the_old_rule(self):
        rng = random.Random(12)
        for _round in range(60):
            trades = rng.sample(["hand", "smith", "miller", "carter"], rng.randrange(1, 4))
            recipe = Recipe("r", {"g": 1.0}, {}, {trade: 5.0 for trade in trades})
            crews = random_crews(rng, trades)
            kept, old = practice.entrant_crew_runs(recipe, crews), old_entrant_crew_runs(recipe, crews)
            self.assertEqual(sorted(kept), sorted(old))
            for trade in old:
                self.assertTrue(math.isclose(kept[trade], old[trade], rel_tol=TOLERANCE))


class EntrantCrewIsShared(unittest.TestCase):

    def test_inside_the_scope_the_crew_is_the_plain_one_and_outside_it_is_not_kept(self):
        rng = random.Random(13)
        producers = {"producer:%d" % index: types.SimpleNamespace(recipe_id=rng.choice("ab"), crew_runs={"hand": rng.uniform(1, 500)})
                     for index in range(25)}
        recipe = Recipe("a", {"g": 1.0}, {}, {"hand": 5.0})
        with entry_practice.shared_crews(producers) as crews:
            self.assertEqual(entry_practice.entrant_crew(recipe, crews("a")), practice.entrant_crew_runs(recipe, crews("a")))
            self.assertEqual(entry_practice.entrant_crew(recipe, crews("b")), practice.entrant_crew_runs(recipe, crews("b")))
        self.assertEqual(entry_practice._entrants, {})
        producers["producer:0"].crew_runs["hand"] = 1.0
        plain = [each.crew_runs for _name, each in sorted(producers.items()) if each.recipe_id == "a"]
        self.assertEqual(entry_practice.entrant_crew(recipe, plain), practice.entrant_crew_runs(recipe, plain))


class HouseholdsFloorPrices(unittest.TestCase):

    def test_memoised_offered_prices_price_the_basket_as_the_plain_read(self):
        class View:
            def area_of(self, good, tile):
                return "area:" + tile

            def offered_price(self, good, area):
                return None if good == "gold" else 1.0 + len(good) + len(area) / 10.0
        basket = Basket((NeedSpec("hunger", 100.0, 1.0, (("bread", 1.0), ("gold", 1.0))),
                         NeedSpec("warmth", 50.0, 1.0, (("wood", 1.0), ("bread", 0.5)))), 0.5, {})
        memo = {}
        for _round in range(3):
            kept = households_close._priced_needs(basket, View(), "tile", memo)
            self.assertEqual(kept, households_basket.need_prices(basket, View(), "tile"))
        self.assertEqual(sorted(memo), [("bread", "tile"), ("gold", "tile"), ("wood", "tile")])


if __name__ == "__main__":
    unittest.main()
