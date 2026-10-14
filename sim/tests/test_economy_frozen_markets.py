"""A market with offers and no bids drifts toward the lowest ask instead of freezing, and the first trade
after such quiet years moves the remembered price only part of the way."""

QUICK_TOPIC = True

import unittest

from sim.economy import market_memory_asks as asks
from sim.economy.market_memory import MarketMemory
from sim.economy.types import EDGE_MINT, Bid, Offer


def offer(ask):
    return Offer("seller", "limestone_kg", "area", "tile", 1.0, ask)


def bid(budget=10.0):
    return Bid("buyer", "limestone_kg", "area", "tile", 1.0, 0.0, 1.0, 0.0, budget)


class NoBidMemoryTests(unittest.TestCase):
    def test_remembered_price_moves_part_of_the_way_to_the_lowest_ask(self):
        price = asks.price_after_no_bids(1000.0, [], [offer(500.0), offer(100.0)])
        self.assertLess(price, 1000.0)
        self.assertGreater(price, 100.0)

    def test_repeated_years_converge_on_the_ask(self):
        price = 1000.0
        for _year in range(30):
            price = asks.price_after_no_bids(price, [], [offer(100.0)]) or price
        self.assertLess(price, 101.0)

    def test_an_ask_above_the_memory_does_not_raise_it(self):
        self.assertIsNone(asks.price_after_no_bids(100.0, [], [offer(900.0)]))

    def test_a_market_with_a_live_bid_is_left_to_the_other_rules(self):
        self.assertIsNone(asks.price_after_no_bids(1000.0, [bid()], [offer(100.0)]))

    def test_a_broke_buyer_is_no_bid(self):
        self.assertIsNotNone(asks.price_after_no_bids(1000.0, [bid(budget=0.0)], [offer(100.0)]))

    def test_nothing_remembered_or_nothing_offered_gives_none(self):
        self.assertIsNone(asks.price_after_no_bids(None, [], [offer(100.0)]))
        self.assertIsNone(asks.price_after_no_bids(1000.0, [], []))


class ResumedTradeTests(unittest.TestCase):
    def test_years_without_bids_are_counted_and_reset(self):
        memory = MarketMemory()
        self.assertEqual(asks.note_bids(memory, "k", [], [offer(1.0)]), 0)
        self.assertEqual(asks.note_bids(memory, "k", [], [offer(1.0)]), 1)
        self.assertEqual(asks.note_bids(memory, "k", [bid()], [offer(1.0)]), 2)
        self.assertEqual(asks.note_bids(memory, "k", [], [offer(1.0)]), 0)

    def test_first_trade_after_quiet_years_moves_part_of_the_way(self):
        price = asks.price_after_resumed_trade(10.0, 1000.0, 3)
        self.assertGreater(price, 10.0)
        self.assertLess(price, 1000.0)

    def test_a_market_that_was_bid_in_adopts_the_volume_rule_price(self):
        self.assertEqual(asks.price_after_resumed_trade(10.0, 1000.0, 0), 1000.0)

    def test_the_count_is_saved_with_the_memory(self):
        self.assertIn("years_without_bids", MarketMemory().__dict__)


class StandingQuoteTests(unittest.TestCase):
    """The mint's bid for the coin metal is a standing price, not what the market's buyers wanted; counted as
    wanted volume it made every trade a sliver and froze the metal's remembered price far below what sellers got."""

    def test_the_mints_standing_bid_is_not_what_the_market_wanted(self):
        households = Bid("household:a", "silver_kg", "area", "tile", 5.0, 0.0, 1.0, 0.0, 1000.0)
        mint = Bid(EDGE_MINT, "silver_kg", "area", "tile", 0.0, 1e9, 1.0, 0.0, float("inf"))
        self.assertEqual(asks.wanted_at([households, mint], 1.0), asks.wanted_at([households], 1.0))

    def test_a_trade_against_a_market_with_only_the_mint_bidding_moves_the_price_most_of_the_way(self):
        mint = Bid(EDGE_MINT, "silver_kg", "area", "tile", 0.0, 1e9, 1.0, 0.0, float("inf"))
        reference = asks.memory_reference_volume(10.0, asks.wanted_at([mint], 300.0))
        self.assertEqual(reference, 10.0)


if __name__ == "__main__":
    unittest.main()
