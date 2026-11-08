"""`goods_respend_rows`: the first round's bids, the offers left and the units bought as columns, against the lists of `Bid` and `Offer`
objects (and the per-buyer lookups) they replace, for markets on the order tables and on the objects. Each test calls one function on
inputs written out or drawn from a seeded generator."""
QUICK_TOPIC = True

import math
import random
import unittest
from operator import attrgetter
from types import SimpleNamespace

import numpy

from sim.book import Book
from sim.economy import goods_respend_rows
from sim.economy.goods_market_rows import MarketRows
from sim.economy.goods_order_book import GoodsOrderBook
from sim.economy.goods_settle import BoughtColumns
from sim.economy.market_tables import MarketTables
from sim.economy.types import Bid, Offer

NAMES = ["farm:a", "farm:b", "baker", "edge:x", "alpha", "Zed", "10", "9"]
TILES = ["t1", "t10", "t2", "A"]


def random_offers(rng, count):
    return [Offer(rng.choice(NAMES), "wheat", "north", rng.choice(TILES), rng.choice([0.0, rng.uniform(0.1, 9.0)]),
                  rng.choice([0.0, 1.5, 1.5, rng.uniform(0.1, 4.0)])) for _each in range(count)]


def random_bids(rng, count):
    return [Bid(rng.choice(NAMES), "wheat", "north", "t1", rng.choice([0.0, rng.uniform(0.0, 20.0)]), rng.choice([0.0, rng.uniform(0.0, 40.0)]),
                rng.choice([0.0, rng.uniform(0.1, 5.0)]), rng.choice([0.5, 1.0, 0.0]), rng.choice([0.0, rng.uniform(1.0, 80.0)]), 1,
                maximum_price=rng.choice([math.inf, rng.uniform(0.5, 6.0)])) for _each in range(count)]


def orders_with(bids, offers):
    orders = GoodsOrderBook(Book(), MarketTables())
    for each in bids:
        orders.add_bid(each)
    for each in offers:
        orders.add_offer(each)
    orders.tables()
    return orders


def reference_offers(offers):
    """The old pack: the offers with units, sorted by (reservation, seller, tile), with their place in the list."""
    places = {id(each): place for place, each in enumerate(offers)}
    ordered = sorted((each for each in offers if each.quantity > 0.0), key=attrgetter("reservation_price", "seller", "tile"))
    return [(each.seller, each.tile, each.reservation_price, each.quantity, places[id(each)]) for each in ordered]


def rows_of(found, agents, tiles):
    return [(agents.names[seller], tiles.names[tile], reservation, quantity, origin) for seller, tile, reservation, quantity, origin in zip(
        found.seller.tolist(), found.tile.tolist(), found.reservation.tolist(), found.quantity.tolist(), found.origin.tolist())]


class OffersLeftAreInClearingOrder(unittest.TestCase):

    def test_a_market_on_the_objects_is_sorted_by_reservation_then_seller_then_tile(self):
        for seed in range(40):
            rng = random.Random(seed)
            offers = random_offers(rng, rng.randint(0, 12))
            market = SimpleNamespace(rows=None, offers=offers)
            agents, tiles = goods_respend_rows.Interner(), goods_respend_rows.Interner()
            found = goods_respend_rows.offer_rows({("wheat", "north"): market}, [("wheat", "north")], None, agents, tiles)
            self.assertEqual(rows_of(found, agents, tiles), reference_offers(offers), seed)
            self.assertEqual(found.market.tolist(), [0] * len(found.market))

    def test_a_market_on_the_tables_is_sorted_the_same_and_keeps_the_places_in_its_rows(self):
        for seed in range(40):
            rng = random.Random(seed)
            first, second = random_offers(rng, rng.randint(0, 8)), random_offers(rng, rng.randint(0, 8))
            orders = orders_with([], first + second)
            markets = {("a", "north"): SimpleNamespace(rows=MarketRows(orders, [], range(len(first))), offers=None),
                       ("b", "north"): SimpleNamespace(rows=MarketRows(orders, [], range(len(first), len(first) + len(second))), offers=None)}
            agents, tiles = goods_respend_rows.Interner(), goods_respend_rows.Interner()
            found = goods_respend_rows.offer_rows(markets, sorted(markets), orders, agents, tiles)
            expected = [(0, *each) for each in reference_offers(first)] + [(1, *each) for each in reference_offers(second)]
            self.assertEqual([(market, *each) for market, each in zip(found.market.tolist(), rows_of(found, agents, tiles))], expected, seed)

    def test_markets_on_the_tables_and_on_the_objects_come_in_market_order(self):
        rng = random.Random(5)
        table_offers, object_offers = random_offers(rng, 6), random_offers(rng, 6)
        orders = orders_with([], table_offers)
        markets = {("a", "n"): SimpleNamespace(rows=None, offers=object_offers),
                   ("b", "n"): SimpleNamespace(rows=MarketRows(orders, [], range(6)), offers=None)}
        agents, tiles = goods_respend_rows.Interner(), goods_respend_rows.Interner()
        found = goods_respend_rows.offer_rows(markets, sorted(markets), orders, agents, tiles)
        self.assertEqual(found.market.tolist(), [0] * len(reference_offers(object_offers)) + [1] * len(reference_offers(table_offers)))
        self.assertEqual(rows_of(found, agents, tiles), reference_offers(object_offers) + reference_offers(table_offers))


class FirstRoundBidsAreTheMarketsBids(unittest.TestCase):

    def test_bids_on_the_tables_and_on_the_objects_keep_their_figures_and_order(self):
        for seed in range(30):
            rng = random.Random(seed)
            table_bids, object_bids = random_bids(rng, rng.randint(1, 8)), random_bids(rng, rng.randint(0, 6))
            orders = orders_with(table_bids, [])
            markets = {("a", "n"): SimpleNamespace(rows=None, bids=object_bids),
                       ("b", "n"): SimpleNamespace(rows=MarketRows(orders, range(len(table_bids)), []), bids=None)}
            agents = goods_respend_rows.Interner()
            found = goods_respend_rows.bid_rows(markets, sorted(markets), orders, agents)
            wanted = [(0, each) for each in object_bids] + [(1, each) for each in table_bids]
            got = sorted(zip(found.market.tolist(), range(len(found.market))))
            self.assertEqual([agents.names[found.buyer[place]] for _market, place in got], [each.buyer for _market, each in wanted], seed)
            for column, name in (("floor", "floor_quantity"), ("flexible", "flexible_quantity"), ("reference", "reference_price"),
                                 ("elasticity", "elasticity"), ("budget", "budget"), ("maximum", "maximum_price")):
                self.assertEqual([getattr(found, column)[place] for _market, place in got], [getattr(each, name) for _market, each in wanted])

    def test_no_markets_have_no_bids(self):
        self.assertEqual(len(goods_respend_rows.bid_rows({}, [], None, goods_respend_rows.Interner()).market), 0)


class UnitsBoughtAreLookedUpPerBid(unittest.TestCase):

    def test_columns_and_dictionaries_give_what_the_buyers_dictionary_gives(self):
        orders = orders_with([Bid("a", "wheat", "n", "t1", 1.0, 1.0, 1.0, 1.0, 5.0, 0), Bid("b", "wheat", "n", "t1", 1.0, 1.0, 1.0, 1.0, 5.0, 0),
                              Bid("c", "wheat", "n", "t1", 1.0, 1.0, 1.0, 1.0, 5.0, 0)], [])
        numbers = {name: orders.book.agent_number(name) for name in "abc"}
        names = orders.book.agent_ids.name_list
        # a was given goods and paid, b only paid (nothing delivered), c was given goods and was not seen paying
        agent = numpy.array([numbers["a"], numbers["b"], numbers["c"]])
        bought = BoughtColumns(names, agent, numpy.array([2.0, 0.0, 3.0]), numpy.array([True, False, True]), numpy.array([-4.0, -1.5, 9.0]),
                               numpy.array([True, True, False]))
        market = SimpleNamespace(rows=MarketRows(orders, range(3), []), bought=bought, bids=None)
        keys = [("wheat", "n")]
        agents = goods_respend_rows.Interner()
        found = goods_respend_rows.bid_rows({keys[0]: market}, keys, orders, agents)
        units, money = goods_respend_rows.bought_columns({keys[0]: market}, keys, found, agents, len(names))
        expected = [bought.get(agents.names[each], (0.0, 0.0)) for each in found.buyer.tolist()]
        self.assertEqual(list(zip(units.tolist(), money.tolist())), expected)
        self.assertEqual(expected, [(2.0, -4.0), (0.0, -1.5), (3.0, 0.0)])

    def test_a_market_with_a_dictionary_is_read_by_name_and_one_without_buyers_gives_zero(self):
        orders = orders_with([Bid("a", "wheat", "n", "t1", 1.0, 1.0, 1.0, 1.0, 5.0, 0), Bid("b", "wheat", "n", "t1", 1.0, 1.0, 1.0, 1.0, 5.0, 0)], [])
        markets = {("wheat", "n"): SimpleNamespace(rows=MarketRows(orders, range(2), []), bought={"b": (4.0, 7.0)}, bids=None),
                   ("wheat", "s"): SimpleNamespace(rows=None, bought={}, bids=[Bid("a", "wheat", "s", "t1", 1.0, 1.0, 1.0, 1.0, 5.0, 0)])}
        keys = sorted(markets)
        agents = goods_respend_rows.Interner()
        found = goods_respend_rows.bid_rows(markets, keys, orders, agents)
        units, money = goods_respend_rows.bought_columns(markets, keys, found, agents, len(orders.book.agent_ids.name_list))
        self.assertEqual(list(zip(found.market.tolist(), [agents.names[each] for each in found.buyer.tolist()], units.tolist(), money.tolist())),
                         [(0, "a", 0.0, 0.0), (0, "b", 4.0, 7.0), (1, "a", 0.0, 0.0)])


class InternerNumbersNames(unittest.TestCase):

    def test_ids_follow_first_sight_and_ranks_follow_the_text_order(self):
        names = goods_respend_rows.Interner()
        self.assertEqual([names.of(each) for each in ["b", "a", "b", "10", "9"]], [0, 1, 0, 2, 3])
        self.assertEqual(names.ranks().tolist(), [3, 2, 0, 1])    # "10" < "9" < "a" < "b" as text
        numbers = names.of_numbers(numpy.array([5, 3, 5]), ["", "", "", "q", "", "b"])
        self.assertEqual(numbers.tolist(), [0, 4, 0])


if __name__ == "__main__":
    unittest.main()
