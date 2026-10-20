"""Two shortcuts taken for speed give the answers of the plain computations they replaced, bit for bit: the
fallback trade read off the registry's flags, and the people of a country by trade."""

QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

from sim.economy import country_figures, labour_state
from sim.economy.setup import labour_area
from sim.labour.market import trades
from sim.labour.market.records import MarketState


class FallbackTradeTests(unittest.TestCase):
    def test_equals_the_fallback_of_the_built_specs(self):
        generator = random.Random(3)
        for _case in range(200):
            registry = {"trade%d" % index: {"family": generator.choice(["a", "b", ""]),
                                           "training_years": generator.choice([None, 0.0, 1.0, 2.5]),
                                           "fallback": generator.random() < 0.2}
                        for index in range(generator.randint(1, 8))}
            self.assertEqual(trades.fallback_trade_of_registry(registry),
                             trades.fallback_trade(trades.trade_specs(registry)))


class CountryPeopleTests(unittest.TestCase):
    def test_equals_the_sum_of_each_tiles_people_by_trade(self):
        generator = random.Random(5)
        state = MarketState()
        tiles = ["t%d" % index for index in range(6)]
        for tile in tiles:
            state.workers[labour_area(tile)] = {
                trade: [generator.uniform(0.0, 50.0) for _band in range(5)]
                for trade in generator.sample(["farmer", "smith", "weaver", "miner"], generator.randint(1, 4))}
        economy = SimpleNamespace(setup=SimpleNamespace(tiles={tile: None for tile in tiles}),
                                  record=SimpleNamespace(workforce=state))
        expected = {}
        for tile in sorted(tiles):
            for trade, people in labour_state.people_by_trade(state, labour_area(tile)).items():
                expected[trade] = expected.get(trade, 0.0) + people
        self.assertEqual(country_figures.people_by_trade(economy, None), dict(sorted(expected.items())))


if __name__ == "__main__":
    unittest.main()
