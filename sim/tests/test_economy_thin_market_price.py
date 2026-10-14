"""A good that trades only a sliver of what the economy wants of it has no national market: one thin area's
price does not stand for the good, which shows near what it costs to make."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy.market_memory import MarketMemory
from sim.economy.notional import shown_prices
from sim.economy.types import Recipe

AREAS = ("a", "b", "c", "d")
MAKING_COST = 2.0 * 3.0 + 4.0 * 0.5


def alloy_game(traded_in_area_a, wanted=100000.0):
    prices = {"alloy|" + area: (900.0 if area == "a" else 10.0) for area in AREAS}
    prices["metal|a"] = 3.0
    memory = MarketMemory(prices=prices, wages={"labour|a": 0.5}, rates={"coin": 0.0})
    memory.volume_weights = {"alloy|a": traded_in_area_a, "metal|a": 500.0}
    memory.note_trading({"alloy|a", "metal|a"})
    record = types.SimpleNamespace(memory=memory, volumes={}, opening_basket={"alloy": wanted},
                                   index_base_prices={})
    recipe = Recipe("melt", {"alloy": 1.0}, {"metal": 2.0}, {"labour": 4.0})
    setup = types.SimpleNamespace(recipes={"melt": recipe}, opening_prices={}, currency_id="coin",
                                  unskilled_trade="labour")
    return setup, record


class ThinMarketTests(unittest.TestCase):
    def test_one_thin_area_does_not_set_the_price_of_a_good_the_economy_wants_in_bulk(self):
        shown, _stale = shown_prices(*alloy_game(traded_in_area_a=2.0))
        self.assertLess(shown["alloy"], 2.0 * MAKING_COST)
        self.assertGreaterEqual(shown["alloy"], MAKING_COST)

    def test_a_market_that_trades_what_is_wanted_keeps_its_market_price(self):
        shown, _stale = shown_prices(*alloy_game(traded_in_area_a=800.0, wanted=1000.0))
        self.assertAlmostEqual(shown["alloy"], 900.0)

    def test_a_good_nobody_can_make_keeps_its_thin_market_price(self):
        setup, record = alloy_game(traded_in_area_a=2.0)
        setup.recipes = {}
        self.assertAlmostEqual(shown_prices(setup, record)[0]["alloy"], 900.0)

    def test_a_good_outside_the_opening_basket_keeps_its_market_price(self):
        setup, record = alloy_game(traded_in_area_a=2.0)
        record.opening_basket = {}
        self.assertAlmostEqual(shown_prices(setup, record)[0]["alloy"], 900.0)


if __name__ == "__main__":
    unittest.main()
