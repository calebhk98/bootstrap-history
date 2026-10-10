"""A partner's coin is worth what it buys at home, which follows the goods, not the wage. A coin valued by the wage
alone made every partner good cheap against home goods once the wage had fallen further than they had, so imports
flowed in and nothing was bought back: money drained and wages fell with it."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy.api import goods_level_over_opening
from sim.economy.market_memory import MarketMemory, market_key
from sim.tests.test_coin_metal_revaluation import Coinage


def record_with(prices, ages):
    memory = MarketMemory()
    memory.prices = {market_key(good, "area"): price for good, price in prices.items()}
    memory.volume_weights = {market_key(good, "area"): 1.0 for good in prices}
    memory.trade_age = {market_key(good, "area"): age for good, age in ages.items()}
    return types.SimpleNamespace(memory=memory, volumes={})


class GoodsLevelTests(unittest.TestCase):
    def test_the_level_is_the_median_price_over_opening_price_of_goods_traded_lately(self):
        record = record_with({"grain": 3.0, "salt": 8.0, "oil": 2.0, "stale": 900.0},
                             {"grain": 0, "salt": 1, "oil": 0, "stale": 40})
        opening = {"grain": 1.0, "salt": 2.0, "oil": 1.0, "stale": 1.0}
        self.assertAlmostEqual(goods_level_over_opening(record, opening), 3.0)   # ratios 3, 4, 2

    def test_no_good_traded_lately_gives_no_level(self):
        record = record_with({"grain": 3.0}, {"grain": 40})
        self.assertIsNone(goods_level_over_opening(record, {"grain": 1.0}))

    def test_a_good_without_an_opening_price_is_left_out(self):
        record = record_with({"grain": 3.0, "new": 50.0}, {"grain": 0, "new": 0})
        self.assertAlmostEqual(goods_level_over_opening(record, {"grain": 1.0}), 3.0)


class CoinValueTests(unittest.TestCase):
    def test_the_coin_metal_is_carried_to_the_goods_level(self):
        game = Coinage()
        flat = game._coin_metal_price("silver_kg")
        game.economy.goods_price_over_wage = lambda: 2.5
        self.assertAlmostEqual(game._coin_metal_price("silver_kg"), flat * 2.5)


if __name__ == "__main__":
    unittest.main()
