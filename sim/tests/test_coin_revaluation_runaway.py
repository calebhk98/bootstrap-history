"""Complaint 135: the coin metal's revaluation is measured in real terms (its price against a fixed basket of
other goods, from the same economy, against the same at the baseline), so the price level it moves cannot move
it back. A loop of price level -> ratio -> price level stays bounded when the metal's real value is unchanged."""

QUICK_TOPIC = True

import types
import unittest

from sim.engine.coin_revaluation import CoinRevaluationMixin
from sim.engine.foreign_payments import ForeignPaymentsMixin
from sim.engine.real_price_ratios import RealPriceRatiosMixin
from sim.engine.wage_market_ratios import WageMarketRatiosMixin

BASELINE = {"silver_kg": 50.0, "wheat_kg": 1.0, "iron_kg": 4.0, "cloth_kg": 9.0}


class AgentCoinage(RealPriceRatiosMixin, CoinRevaluationMixin, WageMarketRatiosMixin, ForeignPaymentsMixin):
    """The agent economy's prices in its own coin; the engine's price level is derived from the ratios."""
    def __init__(self):
        self.state = types.SimpleNamespace(economy=types.SimpleNamespace(
            coin_metal_ratios={}, wage_market_ratios={}, agent_baseline_prices={}, foreign_ledger={}))
        self.civ = {"coin_standard": {"material": "silver_kg"}, "staple": "wheat_kg"}
        self.trade_registry = {}
        self.agent = dict(BASELINE)
        self.economy = types.SimpleNamespace(agent_prices=lambda: self.agent)

    def _home_opening_coin_units(self):
        return 100.0

    def foreign_economies(self):
        return []

    def market_price_ratio(self, material):
        raise AssertionError("the agent economy's price over a cost that follows the price level is never read")


class RunawayTests(unittest.TestCase):
    def years(self, game, count):
        levels = []
        for _year in range(count):
            game.revalue_coin_metals()
            game.record_wage_market_ratios()
            levels.append(game.home_price_level())
        return levels

    def test_an_unchanged_real_value_leaves_the_price_level_alone(self):
        game = AgentCoinage()
        self.years(game, 1)
        game.agent = {good: price * 40.0 for good, price in BASELINE.items()}   # every nominal price scaled
        levels = self.years(game, 12)
        self.assertTrue(all(abs(level - 1.0) < 1e-9 for level in levels), levels)
        self.assertAlmostEqual(game.last_market_price_ratio("wheat_kg"), 1.0)

    def test_a_cheaper_metal_inflates_once_and_settles(self):
        game = AgentCoinage()
        self.years(game, 1)
        game.agent = dict(BASELINE, silver_kg=BASELINE["silver_kg"] / 2.0)
        levels = self.years(game, 30)
        self.assertGreater(levels[-1], 1.5)
        self.assertLess(levels[-1], 2.5)
        self.assertAlmostEqual(levels[-1], levels[-2], places=4)

    def test_a_dearer_staple_shows_in_the_wage_ratio_as_a_relative_price(self):
        game = AgentCoinage()
        self.years(game, 1)
        game.agent = dict(BASELINE, wheat_kg=BASELINE["wheat_kg"] * 3.0)
        self.years(game, 1)
        self.assertGreater(game.last_market_price_ratio("wheat_kg"), 1.5)


if __name__ == "__main__":
    unittest.main()
