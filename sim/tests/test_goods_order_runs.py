"""`goods_order_items.joined_runs` (items that wait one after another from one source are written as one) against writing each item on
its own, as the book's flush did: the same rows in the same order, and the same numbers for agents, goods, tiles and markets, on
written-out items and on seeded random orders from several sources with plain objects between them."""
QUICK_TOPIC = True

import random
import unittest


from sim.book import Book
from sim.economy.goods_order_book import GoodsOrderBook
from sim.economy.goods_order_items import ObjectBids, ObjectOffers, items_of, joined_runs, number_names
from sim.economy.goods_order_tables import HOUSEHOLD, LOAN, OTHER
from sim.economy.market_tables import MarketTables
from sim.economy.order_rows import NamedBids, NamedOffers, OrderRows
from sim.economy.types import Bid, Offer

AGENTS, GOODS, AREAS, TILES = ["a%d" % number for number in range(9)], ["wheat", "iron", "salt", "wine"], ["north", "south"], ["t1", "t2", "t3"]


def new_book() -> GoodsOrderBook:
    return GoodsOrderBook(Book(), MarketTables())


def plain_flush(orders: GoodsOrderBook) -> None:
    """`GoodsOrderBook.flush` with every item written on its own."""
    for waiting, kind, write in ((orders._waiting_bids, ObjectBids, orders._write_bids), (orders._waiting_offers, ObjectOffers, orders._write_offers)):
        items = items_of(waiting, kind)
        number_names(orders, items)
        for item in items:
            write(*item.rows(orders), item.source)
    orders._waiting_bids, orders._waiting_offers = [], []


def fill(orders: GoodsOrderBook, seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(rng.randrange(1, 40)):
        source = rng.choice([HOUSEHOLD, LOAN, OTHER])
        kind = rng.random()
        if kind < 0.2:
            orders.add_bid(Bid(rng.choice(AGENTS), rng.choice(GOODS), rng.choice(AREAS), rng.choice(TILES), 1.0, 2.0, 3.0, 0.5, 9.0, 0), source)
            continue
        if kind < 0.3:
            orders.add_offer(Offer(rng.choice(AGENTS), rng.choice(GOODS), rng.choice(AREAS), rng.choice(TILES), 4.0, 1.5), source)
            continue
        rows = OrderRows(orders, source)
        for _ in range(rng.randrange(1, 3)):
            if rng.random() < 0.7:
                rows.bid(rng.choice(AGENTS), rng.choice(GOODS), rng.choice(AREAS), rng.choice(TILES), rng.random(), rng.random(), rng.random() + 1.0,
                         0.5, rng.random() * 50.0, rng.randrange(3))
            else:
                rows.offer(rng.choice(AGENTS), rng.choice(GOODS), rng.choice(AREAS), rng.choice(TILES), rng.random() * 9.0, rng.random() + 0.5)
        rows.write()


def columns(table):
    count = int(table.row_count[0])
    return {name: getattr(table, name)[:count].tolist() for name in table._fields if name not in ("row_count", "capacity")}


class JoinedRunsTest(unittest.TestCase):
    def test_consecutive_named_bids_of_one_source_become_one_item_in_arrival_order(self):
        def named(buyer, source):
            return NamedBids([buyer], ["wheat"], ["north"], ["t1"], [0], [(1.0, 1.0, 1.0, 0.5, 5.0, float("inf"))], source)
        items = joined_runs([named("a", LOAN), named("b", LOAN), named("c", HOUSEHOLD), named("d", LOAN)])
        self.assertEqual([item.buyer for item in items], [["a", "b"], ["c"], ["d"]])
        self.assertEqual([item.source for item in items], [LOAN, HOUSEHOLD, LOAN])

    def test_named_offers_of_one_source_become_one_item(self):
        first, second = (NamedOffers([seller], ["iron"], ["south"], ["t2"], [3.0], [1.0], LOAN) for seller in ("s1", "s2"))
        (item,) = joined_runs([first, second])
        self.assertEqual((item.seller, item.quantity), (["s1", "s2"], [3.0, 3.0]))

    def test_a_run_of_plain_objects_is_left_alone(self):
        waiting = [(Bid("a", "wheat", "north", "t1", 1.0, 1.0, 1.0, 0.5, 5.0, 0), OTHER)]
        items = items_of(waiting, ObjectBids)
        self.assertEqual(joined_runs(items), items)

    def test_the_tables_and_numbers_equal_those_of_writing_each_item_on_its_own(self):
        for seed in range(40):
            plain, joined = new_book(), new_book()
            fill(plain, seed)
            fill(joined, seed)
            plain_flush(plain)
            joined.flush()
            for kind in ("bids", "offers"):
                self.assertEqual(columns(getattr(joined, kind)), columns(getattr(plain, kind)), (seed, kind))
            for kind in ("agent_ids", "good_ids", "tile_ids"):
                self.assertEqual(getattr(joined.book, kind).name_list, getattr(plain.book, kind).name_list, (seed, kind))
            self.assertEqual(joined.memory_tables.goods_markets.name_list, plain.memory_tables.goods_markets.name_list, seed)


if __name__ == "__main__":
    unittest.main()
