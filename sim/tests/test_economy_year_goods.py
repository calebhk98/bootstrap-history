"""What a goods market that traded nothing tells its sellers about the price next year, and how a
good's price across its areas is summed into one national price."""
import types
import unittest

from sim.economy.market_memory import MarketMemory
from sim.economy.types import Bid, Offer
from sim.economy.accounts import Book
from sim.economy.types import EDGE_CONSUMPTION, EDGE_PRODUCTION, GoodsMove
from sim.economy.year_close import held_only, learned_prices, national_prices
from sim.economy.year_goods import _unsold_signal


def bid(maximum_price):
    return Bid("buyer", "timber", "area", "tile", 10.0, 0.0, 1.0, 1.0, 1e9, 0, maximum_price=maximum_price)


def offer(reservation, quantity=5.0):
    return Offer("seller", "timber", "area", "tile", quantity, reservation)


class UnsoldSignalTests(unittest.TestCase):
    def test_sellers_asking_above_every_buyer_learn_the_most_a_buyer_would_pay(self):
        self.assertEqual(_unsold_signal([bid(3.0), bid(4.0)], [offer(6.0)]), 4.0)

    def test_a_seller_asking_less_than_buyers_pay_learns_nothing_from_a_dry_market(self):
        # nothing traded because nothing real was on offer (rounding dust), not because the ask was too high
        self.assertIsNone(_unsold_signal([bid(3.0), bid(4.0)], [offer(0.0, quantity=1e-10)]))

    def test_no_offers_no_signal(self):
        self.assertIsNone(_unsold_signal([bid(4.0)], []))


class NationalPriceTests(unittest.TestCase):
    def test_areas_are_weighted_by_what_they_usually_trade_not_this_year_alone(self):
        # an area that trades only in alternate years must not swing the national price each year
        memory = MarketMemory(prices={"tin|a": 1.0, "tin|b": 10.0}, volume_weights={"tin|a": 70.0, "tin|b": 30.0})
        record = types.SimpleNamespace(memory=memory, volumes={"tin|a": 0.0, "tin|b": 100.0})
        self.assertAlmostEqual(national_prices(record)["tin"], 0.7 * 1.0 + 0.3 * 10.0)

    def test_a_market_that_stops_trading_keeps_part_of_its_weight(self):
        memory = MarketMemory()
        memory.note_volume("tin|a", 100.0)
        memory.note_volume("tin|a", 0.0)
        self.assertGreater(memory.volume_weights["tin|a"], 0.0)
        self.assertLess(memory.volume_weights["tin|a"], 100.0)


class LearnedPriceTests(unittest.TestCase):
    def test_a_market_that_sold_nothing_teaches_the_most_a_buyer_would_pay(self):
        # the clearing result of a dry market carries last year's price; the memory carries the signal
        clearing = types.SimpleNamespace(good="tin", area="a", price=20.0, quantity=0.0)
        memory = MarketMemory(prices={"tin|a": 3.0})
        prices, volumes = learned_prices([clearing], memory)
        self.assertEqual(prices[("tin", "a")], 3.0)
        self.assertEqual(volumes[("tin", "a")], 0.0)


class ConsumptionTests(unittest.TestCase):
    def test_an_agent_consumes_what_it_holds_when_its_fills_say_a_hair_more(self):
        book = Book()
        book.move_many([GoodsMove(EDGE_PRODUCTION, "household", "oil", "tile", 1.0, "test")])
        moves = held_only([GoodsMove("household", EDGE_CONSUMPTION, "oil", "tile", 1.0 + 4e-9, "eaten")], book)
        book.move_many(moves)
        self.assertEqual(book.stock("household", "oil", "tile"), 0.0)


if __name__ == "__main__":
    unittest.main()
