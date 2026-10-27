"""Every reader of a market's price can tell a traded price from a quote or an estimate (Complaint 642): the memory
names the kind, the shown prices carry it, and a reader never turns a missing price into zero."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import notional, types as economy_types
from sim.economy.market_memory import PRICE_TRADED, MarketMemory
from sim.economy.notional import KIND_MAKING_COST_ESTIMATE, KIND_REMEMBERED, shown_prices_with_kinds
from sim.economy.types import QUOTE_BEST_UNFILLED_BID, QUOTE_OPENING_ESTIMATE, Recipe
from sim.markets.port_actors import standing_price
from sim.ui.proto.render_screens_market import NO_TRADE_CAUSE, price_note


def memory_with(prices, cleared=(), quotes=None):
    memory = MarketMemory(prices=dict(prices), wages={"labour|a": 0.5}, rates={"coin": 0.0})
    memory.cleared_prices = {key: prices[key] for key in cleared}
    memory.quote_kinds = dict(quotes or {})
    return memory


class MemoryNamesWhatAPriceIsTests(unittest.TestCase):
    def test_a_price_a_market_cleared_at_is_traded(self):
        memory = memory_with({"grain|a": 3.0}, cleared=["grain|a"])
        self.assertEqual(memory.price_kind("grain|a"), PRICE_TRADED)

    def test_a_price_nothing_traded_at_is_its_quote_kind(self):
        memory = memory_with({"grain|a": 3.0}, quotes={"grain|a": QUOTE_BEST_UNFILLED_BID})
        self.assertEqual(memory.price_kind("grain|a"), QUOTE_BEST_UNFILLED_BID)

    def test_a_price_no_clearing_has_replaced_is_the_opening_estimate(self):
        self.assertEqual(memory_with({"grain|a": 3.0}).price_kind("grain|a"), QUOTE_OPENING_ESTIMATE)

    def test_a_market_with_no_price_has_no_kind(self):
        self.assertIsNone(memory_with({}).price_kind("grain|a"))

    def test_a_good_is_traded_when_any_of_its_markets_traded(self):
        memory = memory_with({"grain|a": 3.0, "grain|b": 4.0}, cleared=["grain|b"],
                             quotes={"grain|a": QUOTE_BEST_UNFILLED_BID})
        self.assertEqual(memory.price_kinds_by_good(), {"grain": PRICE_TRADED})

    def test_a_good_none_of_whose_markets_traded_is_never_shown_as_traded(self):
        memory = memory_with({"grain|a": 3.0, "grain|b": 4.0}, quotes={"grain|b": QUOTE_BEST_UNFILLED_BID})
        self.assertNotEqual(memory.price_kinds_by_good()["grain"], PRICE_TRADED)


def shown_game():
    """Grain traded last year; metal did not, and its remembered price is a quote."""
    memory = memory_with({"grain|a": 3.0, "metal|a": 50.0}, cleared=["grain|a"],
                         quotes={"metal|a": QUOTE_BEST_UNFILLED_BID})
    memory.trade_age = {"grain|a": 1, "metal|a": 99}
    record = types.SimpleNamespace(memory=memory, volumes={}, opening_basket={}, index_base_prices={})
    recipes = {"smelt": Recipe("smelt", {"metal": 1.0}, {}, {"labour": 2.0})}
    setup = types.SimpleNamespace(recipes=recipes, opening_prices={}, currency_id="coin", unskilled_trade="labour")
    return setup, record


class ShownPricesCarryTheirKindTests(unittest.TestCase):
    def test_a_traded_good_is_shown_as_traded(self):
        _prices, _stale, kinds = shown_prices_with_kinds(*shown_game())
        self.assertEqual(kinds["grain"], PRICE_TRADED)

    def test_an_untraded_good_somebody_makes_is_shown_as_its_making_cost(self):
        prices, stale, kinds = shown_prices_with_kinds(*shown_game())
        self.assertIn("metal", stale)
        self.assertEqual(kinds["metal"], KIND_MAKING_COST_ESTIMATE)
        self.assertAlmostEqual(prices["metal"], 2.0 * 0.5)

    def test_an_untraded_good_nobody_makes_is_shown_as_the_quote_it_is(self):
        setup, record = shown_game()
        setup.recipes = {}
        _prices, stale, kinds = shown_prices_with_kinds(setup, record)
        self.assertIn("metal", stale)
        self.assertEqual(kinds["metal"], QUOTE_BEST_UNFILLED_BID)

    def test_a_stale_price_with_no_quote_is_the_opening_estimate_not_a_trade(self):
        setup, record = shown_game()
        setup.recipes = {}
        record.memory.quote_kinds = {}
        _prices, _stale, kinds = shown_prices_with_kinds(setup, record)
        self.assertIn(kinds["metal"], (QUOTE_OPENING_ESTIMATE, KIND_REMEMBERED))


class ReadersDoNotInventAPriceTests(unittest.TestCase):
    def test_a_standing_bid_has_no_price_where_there_is_none(self):
        self.assertIsNone(standing_price(None, None))
        self.assertIsNone(standing_price(None, 0.0))

    def test_a_standing_bid_follows_the_planning_price_then_the_opening_one(self):
        self.assertEqual(standing_price(4.0, 9.0), 4.0)
        self.assertEqual(standing_price(None, 9.0), 9.0)


class PlayerSeesNoTradeWithItsCauseTests(unittest.TestCase):
    # presentation: the note on the market screen's row
    def test_a_quote_is_noted_as_no_trade_with_its_cause(self):
        note = price_note({"price_kind": QUOTE_BEST_UNFILLED_BID, "price_basis": "solved"})
        self.assertTrue(note.startswith("no trade"), note)

    def test_a_traded_price_carries_no_such_note(self):
        self.assertEqual(price_note({"price_kind": PRICE_TRADED, "price_basis": "solved"}), "")

    def test_every_quote_and_estimate_kind_has_a_cause(self):
        kinds = {getattr(economy_types, name) for name in dir(economy_types) if name.startswith("QUOTE_")}
        kinds |= {getattr(notional, name) for name in dir(notional) if name.startswith("KIND_")}
        self.assertEqual(kinds - set(NO_TRADE_CAUSE), set())


if __name__ == "__main__":
    unittest.main()
