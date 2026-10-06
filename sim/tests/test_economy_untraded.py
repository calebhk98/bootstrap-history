"""A price a market has not cleared lately is not a market price: it is aged, kept out of the price
index, and (for a good somebody can make) follows what it costs to make at today's prices."""
import dataclasses
import types
import unittest

from sim.economy.market_memory import MarketMemory
from sim.economy.notional import notional_prices, recently_traded_goods, shown_prices
from sim.economy.types import Recipe
from sim.economy.year_close import remember_basket_price_level


def setup_with(recipes, opening):
    return types.SimpleNamespace(recipes=recipes, opening_prices=opening, currency_id="coin", unskilled_trade="labour")


def record_with(memory, basket, base=None):
    return types.SimpleNamespace(memory=memory, volumes={}, opening_basket=basket, index_base_prices=base or {})


class TradeAgeTests(unittest.TestCase):
    def test_a_market_that_never_cleared_has_no_age_and_a_cleared_one_ages_each_idle_year(self):
        memory = MarketMemory(prices={"tin|a": 1.0, "salt|a": 1.0})
        self.assertIsNone(memory.years_since_trade("tin|a"))
        memory.note_trading({"tin|a"})
        self.assertEqual(memory.years_since_trade("tin|a"), 0)
        memory.note_trading(set())
        memory.note_trading(set())
        self.assertEqual(memory.years_since_trade("tin|a"), 2)
        self.assertIsNone(memory.years_since_trade("salt|a"))

    def test_the_age_is_saved_with_the_memory(self):
        memory = MarketMemory(prices={"tin|a": 1.0})
        memory.note_trading({"tin|a"})
        self.assertEqual(dataclasses.asdict(memory)["trade_age"], {"tin|a": 0})

    def test_a_good_counts_as_traded_while_any_of_its_areas_cleared_recently(self):
        memory = MarketMemory(prices={"tin|a": 1.0, "tin|b": 1.0, "salt|a": 1.0})
        memory.note_trading({"tin|b"})
        self.assertEqual(recently_traded_goods(memory), {"tin"})
        for _year in range(10):
            memory.note_trading(set())
        self.assertEqual(recently_traded_goods(memory), set())


class PriceLevelTests(unittest.TestCase):
    def test_goods_that_have_not_traded_do_not_hold_the_index_at_their_old_price(self):
        memory = MarketMemory(prices={"tin|a": 2.0, "salt|a": 1.0})
        memory.note_trading({"tin|a"})
        base = {"tin": 1.0, "salt": 1.0}
        record = record_with(memory, {"tin": 1.0, "salt": 1.0}, base)
        self.assertAlmostEqual(remember_basket_price_level(setup_with({}, base), record), 2.0)

    def test_with_nothing_traded_the_level_is_unchanged(self):
        memory = MarketMemory(prices={"tin|a": 2.0})
        record = record_with(memory, {"tin": 1.0}, {"tin": 1.0})
        self.assertEqual(remember_basket_price_level(setup_with({}, {"tin": 1.0}), record), 1.0)


def smelt():
    return Recipe("smelt", {"tin": 2.0}, {"ore": 4.0}, {"labour": 10.0})


class NotionalPriceTests(unittest.TestCase):
    def memory(self):
        memory = MarketMemory(prices={"ore|a": 3.0, "tin|a": 99.0}, wages={"labour|a": 0.5}, rates={"coin": 0.0})
        memory.note_trading({"ore|a"})
        return memory

    def test_an_untraded_good_follows_the_cost_of_making_it_at_todays_prices(self):
        record = record_with(self.memory(), {})
        prices = notional_prices(setup_with({"smelt": smelt()}, {"tin": 99.0}), record)
        self.assertAlmostEqual(prices["tin"], (4.0 * 3.0 + 10.0 * 0.5) / 2.0)

    def test_a_traded_good_has_no_notional_price(self):
        memory = self.memory()
        memory.note_trading({"ore|a", "tin|a"})
        self.assertNotIn("tin", notional_prices(setup_with({"smelt": smelt()}, {}), record_with(memory, {})))

    def test_a_good_whose_maker_cannot_be_priced_gets_none(self):
        memory = MarketMemory(prices={"tin|a": 99.0}, wages={"labour|a": 0.5})
        self.assertNotIn("tin", notional_prices(setup_with({"smelt": smelt()}, {}), record_with(memory, {})))

    def test_a_cost_chains_through_an_untraded_input(self):
        alloy = Recipe("alloy", {"bronze": 1.0}, {"tin": 1.0}, {})
        memory = self.memory()
        memory.prices["bronze|a"] = 50.0
        prices = notional_prices(setup_with({"smelt": smelt(), "alloy": alloy}, {}), record_with(memory, {}))
        self.assertAlmostEqual(prices["bronze"], prices["tin"])

    def test_the_game_sees_cost_for_a_made_good_and_the_stale_last_price_otherwise(self):
        memory = self.memory()
        memory.prices["salt|a"] = 7.0
        shown, stale = shown_prices(setup_with({"smelt": smelt()}, {}), record_with(memory, {}))
        self.assertAlmostEqual(shown["tin"], 8.5)
        self.assertEqual(shown["salt"], 7.0)
        self.assertEqual(shown["ore"], 3.0)
        self.assertEqual(stale, {"tin", "salt"})
        self.assertNotIn("ore", stale)


if __name__ == "__main__":
    unittest.main()
