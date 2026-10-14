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


def alloy_of_untraded_metal_game():
    """The alloy trades a sliver; the metal it is melted from does not trade, and its stale price is far above
    what the metal costs to make."""
    prices = {"alloy|a": 900.0, "metal|a": 50.0}
    memory = MarketMemory(prices=prices, wages={"labour|a": 0.5}, rates={"coin": 0.0})
    memory.volume_weights = {"alloy|a": 2.0}
    memory.note_trading({"alloy|a"})
    record = types.SimpleNamespace(memory=memory, volumes={}, opening_basket={"alloy": 100000.0},
                                   index_base_prices={})
    recipes = {"melt": Recipe("melt", {"alloy": 1.0}, {"metal": 2.0}, {"labour": 4.0}),
               "smelt": Recipe("smelt", {"metal": 1.0}, {}, {"labour": 2.0})}
    setup = types.SimpleNamespace(recipes=recipes, opening_prices={}, currency_id="coin", unskilled_trade="labour")
    return setup, record


class ThinMarketTests(unittest.TestCase):
    def test_a_thin_good_is_costed_at_what_its_untraded_input_costs_to_make_not_its_stale_price(self):
        shown, _stale = shown_prices(*alloy_of_untraded_metal_game())
        metal_cost = 2.0 * 0.5
        self.assertAlmostEqual(shown["metal"], metal_cost)
        self.assertLess(shown["alloy"], 2.0 * (2.0 * metal_cost + 4.0 * 0.5))

    def test_one_thin_area_does_not_set_the_price_of_a_good_the_economy_wants_in_bulk(self):
        shown, _stale = shown_prices(*alloy_game(traded_in_area_a=2.0))
        self.assertLess(shown["alloy"], 2.0 * MAKING_COST)
        self.assertGreaterEqual(shown["alloy"], MAKING_COST)

    def test_a_market_that_usually_trades_a_lot_but_traded_a_sliver_this_year_shows_near_its_making_cost(self):
        setup, record = alloy_game(traded_in_area_a=800.0)
        record.volumes = {"alloy|a": 2.0, "metal|a": 500.0}
        shown, _stale = shown_prices(setup, record)
        self.assertLess(shown["alloy"], 2.0 * MAKING_COST)

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
