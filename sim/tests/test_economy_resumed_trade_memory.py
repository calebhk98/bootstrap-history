"""A sliver of trade after years with buyers and no seller must not reset the remembered price."""
import types
import unittest

from sim.economy import year_goods
from sim.economy.accounts import Book
from sim.economy.market_memory import MarketMemory, market_key
from sim.economy.types import EDGE_ISSUE, EDGE_PRODUCTION, Bid, GoodsMove, Offer, Transfer
from sim.economy.year_ledger import YearLedger

CURRENCY = "coin"
KEY = market_key("brass", "area")


def one_year(memory, book, bids, offers):
    setup = types.SimpleNamespace(recipes={}, tax_forms=[], currency_id=CURRENCY, opening_prices={"brass": 4.0},
                                  specs={}, state_agent="state", port_tile=None)
    record = types.SimpleNamespace(producers={}, memory=memory, book=book, volumes={})
    order_book = {("brass", "area"): (list(bids), list(offers))}
    year_goods.clear_goods(setup, record, None, None, order_book, {}, YearLedger())


def household_bid():
    # flexible demand for a good bought for variety: no ceiling, budget-limited
    return Bid("household", "brass", "area", "tile", 0.0, 1000.0, 4.0, 2.0, 4000.0, 1)


def funded_book(quantity):
    book = Book()
    book.transfer(Transfer(EDGE_ISSUE, "household", CURRENCY, 1e9, "seed"))
    if quantity > 0.0:
        book.move(GoodsMove(EDGE_PRODUCTION, "smith", "brass", "tile", quantity, "seed"))
    return book


class ResumedAfterDryYears(unittest.TestCase):
    def memory(self, dry_years):
        memory = MarketMemory(prices={KEY: 4.0}, volume_weights={KEY: 500.0}, trade_age={KEY: 0})
        for _year in range(dry_years):          # buyers and no seller, as the game plays it
            one_year(memory, funded_book(0.0), [household_bid()], [])
        return memory

    def test_sliver_of_trade_after_dry_years_cannot_reset_the_memory(self):
        memory = self.memory(30)
        sliver = Offer("smith", "brass", "area", "tile", 0.11, 0.1)
        one_year(memory, funded_book(0.11), [household_bid()], [sliver])
        self.assertLess(memory.prices[KEY], 4.0 * 6.0)

    def test_real_supply_after_dry_years_still_brings_the_memory_to_the_market_price(self):
        def full_years(memory):
            for _year in range(8):
                one_year(memory, funded_book(500.0), [household_bid()], [Offer("smith", "brass", "area", "tile", 500.0, 0.1)])
            return memory.prices[KEY]
        ordinary = full_years(MarketMemory(prices={KEY: 4.0}, volume_weights={KEY: 500.0}, trade_age={KEY: 0}))
        after_dry = full_years(self.memory(3))
        self.assertAlmostEqual(after_dry / ordinary, 1.0, delta=0.05)

    def test_sliver_in_a_market_that_never_cleared_cannot_move_the_opening_estimate_far(self):
        memory = MarketMemory(prices={KEY: 4.0})        # opening estimate: no usual volume, never cleared
        sliver = Offer("smith", "brass", "area", "tile", 0.11, 0.1)
        one_year(memory, funded_book(0.11), [household_bid()], [sliver])
        self.assertLess(memory.prices[KEY], 4.0 * 6.0)

    def test_ordinary_market_still_follows_its_price(self):
        memory = MarketMemory(prices={KEY: 4.0}, volume_weights={KEY: 500.0}, trade_age={KEY: 0})
        one_year(memory, funded_book(500.0), [household_bid()], [Offer("smith", "brass", "area", "tile", 500.0, 0.1)])
        self.assertNotEqual(memory.prices[KEY], 4.0)


if __name__ == "__main__":
    unittest.main()
