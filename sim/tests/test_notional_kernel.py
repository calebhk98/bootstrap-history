"""`notional_kernel.cost_estimates` gives, to the last bit, what the good-by-good loops of `notional` gave (`cheapest_cost` over
`input_depth_order`, with and without the estimates feeding the goods after them and the thin-market blend), on random recipes with
joint outputs, plants of every life, missing prices and wages and goods in cycles; no game."""

QUICK_TOPIC = True

import math
import random
import unittest

from sim.economy import notional
from sim.economy.notional_kernel import COSTS_ONLY, ESTIMATES, cost_estimates
from sim.economy.recipes import input_depth_order
from sim.economy.types import Recipe

GOODS = ["good%02d" % each for each in range(14)]
TRADES = ["labourer", "smith", "miller", "clerk"]
SHARE = 0.1


def random_recipes(rng):
    recipes = {}
    for index in range(rng.randrange(6, 20)):
        outputs = {good: rng.choice((0.0, rng.uniform(0.2, 3.0))) for good in rng.sample(GOODS, rng.randrange(1, 4))}
        recipes["r%d" % index] = Recipe(
            "r%d" % index, outputs, {good: rng.uniform(0.1, 4.0) for good in rng.sample(GOODS, rng.randrange(0, 4))},
            {trade: rng.uniform(0.0, 5.0) for trade in rng.sample(TRADES, rng.randrange(0, 3))},
            {good: rng.uniform(0.5, 6.0) for good in rng.sample(GOODS, rng.randrange(0, 3))},
            {trade: rng.uniform(1.0, 20.0) for trade in rng.sample(TRADES, rng.randrange(0, 2))}, rng.choice((0.0, 5.0, 30.0)))
    return recipes


def random_prices(rng):
    live = {good: rng.uniform(0.1, 20.0) for good in GOODS if rng.random() < 0.7}
    wages = {trade: rng.uniform(0.1, 3.0) for trade in TRADES if rng.random() < 0.85}
    return live, wages


def setup_of(recipes):
    class Setup:
        pass
    setup = Setup()
    setup.recipes = recipes
    return setup


def costs_one_by_one(recipes, live, wages, rate):
    """`notional.making_costs`'s loop before the kernel."""
    costs = {}
    for good in input_depth_order(recipes):
        best = notional.cheapest_cost(setup_of(recipes), good, live, wages, rate)
        if best is not None:
            costs[good] = best
    return costs


def estimates_one_by_one(recipes, market, wages, rate, recent, thin, wanted_of, traded):
    """`notional._estimated_prices`'s loop before the kernel."""
    live, estimated = dict(market), {}
    for good in input_depth_order(recipes):
        if good not in recent:
            cost = notional.cheapest_cost(setup_of(recipes), good, live, wages, rate)
            if cost is not None:
                estimated[good] = live[good] = cost
            continue
        wanted = wanted_of.get(good, 0.0)
        if not thin or wanted <= 0.0 or good not in live:
            continue
        depth = min(1.0, traded.get(good, 0.0) / (SHARE * wanted))
        if depth >= 1.0:
            continue
        cost = notional.cheapest_cost(setup_of(recipes), good, live, wages, rate)
        if cost is not None:
            estimated[good] = live[good] = depth * live[good] + (1.0 - depth) * cost
    return estimated


class CostEstimates(unittest.TestCase):
    def test_every_good_costs_what_the_one_by_one_loop_gives_in_value_and_order(self):
        compared = 0
        for seed in range(40):
            rng = random.Random(seed)
            recipes, (live, wages), rate = random_recipes(rng), random_prices(rng), rng.choice((0.0, 1e-12, 0.04, 0.3))
            new, old = cost_estimates(COSTS_ONLY, recipes, live, wages, rate), costs_one_by_one(recipes, live, wages, rate)
            self.assertEqual(list(new), list(old), seed)
            self.assertEqual(new, old, seed)
            compared += len(old)
        self.assertGreater(compared, 100)

    def test_the_estimates_feed_the_goods_after_them_and_the_thin_goods_are_blended(self):
        compared = blended = 0
        for seed in range(40):
            rng = random.Random(1000 + seed)
            recipes, (live, wages), rate = random_recipes(rng), random_prices(rng), rng.choice((0.0, 0.04, 0.3))
            recent = {good for good in GOODS if rng.random() < 0.5}
            wanted = {good: rng.choice((0.0, rng.uniform(1.0, 100.0))) for good in GOODS}
            traded = {good: rng.uniform(0.0, 12.0) for good in GOODS if rng.random() < 0.8}
            for thin in (False, True):
                new = cost_estimates(ESTIMATES, recipes, live, wages, rate, recent, thin, wanted, traded, SHARE)
                old = estimates_one_by_one(recipes, live, wages, rate, recent, thin, wanted, traded)
                self.assertEqual(list(new), list(old), (seed, thin))
                self.assertEqual(new, old, (seed, thin))
                compared += len(old)
                blended += sum(1 for good in old if good in recent)
        self.assertGreater(compared, 100)
        self.assertGreater(blended, 5, "the thin-market blend is part of what is compared")

    def test_a_good_nothing_makes_has_no_estimate_and_a_cost_is_positive_and_finite(self):
        recipes = {"r": Recipe("r", {"b": 1.0}, {"a": 1.0}, {}, {}, {}, 0.0)}
        found = cost_estimates(COSTS_ONLY, recipes, {"a": 2.0}, {}, 0.05)
        self.assertEqual(found, {"b": 2.0})
        self.assertTrue(all(math.isfinite(value) and value > 0.0 for value in found.values()))

    def test_a_run_whose_input_has_no_price_is_unpriceable(self):
        recipes = {"r": Recipe("r", {"b": 1.0}, {"a": 1.0}, {}, {}, {}, 0.0)}
        self.assertEqual(cost_estimates(COSTS_ONLY, recipes, {}, {}, 0.05), {})


if __name__ == "__main__":
    unittest.main()
