"""Scenario, Complaint 473: the Rome game's opening basket agrees with the supply its opening builds, good by good, and
the price level index starts at one. The rule on the fixture economy is in test_opening_basket_agrees."""
import unittest

from sim.economy import api as economy_api
from sim.tests import harness
from sim.tests.test_opening_basket_agrees import goods_over_supply


class RomeOpeningBasketTests(unittest.TestCase):
    def test_no_good_in_the_rome_basket_exceeds_its_supply_and_the_index_starts_at_one(self):
        from sim.engine.economy_port_setup import build_setup
        game = harness.unopened_sim()
        setup = build_setup(game)
        economy = economy_api.blank_economy(setup)
        self.assertEqual(goods_over_supply(setup, economy.record), {})
        weights = economy.record.opening_basket
        from sim.economy import currency
        self.assertEqual(currency.basket_price_level(setup.opening_prices, setup.opening_prices, weights), 1.0)


if __name__ == "__main__":
    unittest.main()
