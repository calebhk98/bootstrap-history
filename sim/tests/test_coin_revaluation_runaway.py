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

    def test_unchanged_scarcity_keeps_the_price_level_in_a_narrow_band(self):
        game = AgentCoinage()
        self.years(game, 1)
        levels = self.years(game, 40)
        self.assertTrue(all(abs(level - 1.0) < 1e-9 for level in levels), levels)

    def test_a_spike_in_the_metals_own_price_does_not_move_the_level(self):
        game = AgentCoinage()
        self.years(game, 1)
        levels = []
        for year in range(12):
            game.agent = dict(BASELINE, silver_kg=BASELINE["silver_kg"] * 2.0 ** year)   # the metal alone runs away
            levels += self.years(game, 1)
        self.assertTrue(all(abs(level - 1.0) < 1e-9 for level in levels), levels)

    def test_goods_pricing_twice_the_coin_raises_the_level_once_and_settles(self):
        game = AgentCoinage()
        self.years(game, 1)
        game.agent = {good: (price if good == "silver_kg" else price * 2.0) for good, price in BASELINE.items()}
        levels = self.years(game, 40)
        self.assertAlmostEqual(levels[-1], 2.0, places=3)
        self.assertLess(max(levels), 2.0 + 1e-6)
        self.assertEqual(levels, sorted(levels))
        self.assertAlmostEqual(levels[-1], levels[-2], places=6)

    def test_one_years_move_is_capped(self):
        game = AgentCoinage()
        self.years(game, 1)
        game.agent = {good: (price if good == "silver_kg" else price * 100.0) for good, price in BASELINE.items()}
        self.assertLess(self.years(game, 1)[0], 1.25 + 1e-9)

    def test_a_dearer_staple_shows_in_the_wage_ratio_as_a_relative_price(self):
        game = AgentCoinage()
        self.years(game, 1)
        game.agent = dict(BASELINE, wheat_kg=BASELINE["wheat_kg"] * 3.0)
        self.years(game, 1)
        self.assertGreater(game.last_market_price_ratio("wheat_kg"), 1.5)


if __name__ == "__main__":
    unittest.main()
