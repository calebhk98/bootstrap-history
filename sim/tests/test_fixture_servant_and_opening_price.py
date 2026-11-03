"""The fixture setups name a servant trade the wage rule can price, and a late good's opening price is read in today's money.

sim/economy/fixture_setups.py, sim/economy/land_bid_year.py, sim/economy/setup.py (opening_price_today).
"""
QUICK_TOPIC = True

import types
import unittest

from sim.economy import fixture_setups, land_bid_year
from sim.economy.setup import opening_price_today


class StandInView:
    """Answers a wage and a wage level as a bare market view would; no prices."""

    def wage(self, trade, area):
        return {fixture_setups.LABOURER: 1.0}.get(trade)

    def opening_wage_level(self, currency):
        return 1.0


class FixtureServantTest(unittest.TestCase):
    def test_small_setup_names_a_servant_trade_the_setup_holds(self):
        setup = fixture_setups.small_setup()
        self.assertIn(setup.servant_trade, setup.opening_wages)

    def test_best_margin_prices_the_servant_trade(self):
        setup = fixture_setups.small_setup()
        cohort = types.SimpleNamespace(tile=fixture_setups.TOWN)
        margin = land_bid_year.best_margin(setup, StandInView(), cohort, {}, None)
        self.assertEqual(margin, (0.0, 0.0, ""))


class OpeningPriceTodayTest(unittest.TestCase):
    def test_scales_by_the_memory_wage_level(self):
        setup = types.SimpleNamespace(opening_prices={"grain": 2.0}, currency_id="coin")
        memory = types.SimpleNamespace(opening_wage_level=lambda currency: 3.0)
        self.assertEqual(opening_price_today(setup, memory, "grain"), 6.0)

    def test_none_without_an_opening_price(self):
        setup = types.SimpleNamespace(opening_prices={}, currency_id="coin")
        memory = types.SimpleNamespace(opening_wage_level=lambda currency: 3.0)
        self.assertIsNone(opening_price_today(setup, memory, "grain"))


if __name__ == "__main__":
    unittest.main()
