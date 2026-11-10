"""`settlement_ids.settle_by_ids` against `settlement_arrays.settle_results` (the old path through `KeyTable` and `Settlement` objects) on
the same traded markets of one hand-made batch: the same listed agents and keys in the same order, the same sums and goods moved
per market, and the same book afterwards (balances, stocks, gross totals). Random pairs on random purses and stocks, so a purse
or a stock too small for what its owner owes or sold is scaled down in both. Also the numbering helpers on written-out inputs
(under numba and ROME_NO_JIT=1)."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

import numpy

from sim.book import Book
from sim.economy import settlement_arrays
from sim.economy.goods_order_book import GoodsOrderBook
from sim.economy.goods_table_results import TableClearing
from sim.economy.goods_table_views import TableBatch
from sim.economy.market_tables import MarketTables
from sim.economy.settlement_ids import settle_by_ids
from sim.economy.settlement_numbering import local_numbering
from sim.economy.types import EDGE_MINT, Bid, GoodsMove, Offer, Transfer

MONEY, GOOD = "coin", "grain"
BUYERS, SELLERS = ("b1", "b2", "b3", "b4"), ("s1", "s2", "s3", EDGE_MINT)
TILES = ("t1", "t2", "")


def scenario(seed):
    """(orders, batch, results) of a random batch of three traded markets on funded agents."""
    rng = random.Random(seed)
    orders = GoodsOrderBook(Book(), MarketTables())
    book = orders.book
    bid_rows, offer_rows, bid_ptr, offer_ptr, pair_ptr = [], [], [0], [0], [0]
    pair_bid, pair_offer, pair_quantity, asks = [], [], [], []
    for area in ("north", "south", "east"):
        first_bid, first_offer = len(bid_rows), len(offer_rows)
        for _ in range(rng.randrange(1, 5)):
            orders.add_bid(Bid(rng.choice(BUYERS), GOOD, area, rng.choice(TILES), 1.0, 1.0, 2.0, 0.5, 50.0, 0))
            bid_rows.append(orders.bid_count() - 1)
        for _ in range(rng.randrange(1, 4)):
            orders.add_offer(Offer(rng.choice(SELLERS), GOOD, area, rng.choice(TILES[:2]), 5.0, 1.0))
            offer_rows.append(orders.offer_count() - 1)
        asks.extend(rng.uniform(0.5, 4.0) for _ in offer_rows[first_offer:])
        for _ in range(rng.randrange(1, 6)):
            pair_bid.append(first_bid + rng.randrange(len(bid_rows) - first_bid))
            pair_offer.append(first_offer + rng.randrange(len(offer_rows) - first_offer))
            pair_quantity.append(rng.uniform(0.2, 6.0))
        bid_ptr.append(len(bid_rows))
        offer_ptr.append(len(offer_rows))
        pair_ptr.append(len(pair_bid))
    for name in BUYERS + SELLERS[:-1]:
        book.post([Transfer(EDGE_MINT, name, MONEY, rng.choice([0.0, 3.0, 30.0, 400.0]), "start")], [])
    for name in SELLERS[:-1]:
        for tile in TILES[:2]:
            book.post([], [GoodsMove(EDGE_MINT, name, GOOD, tile, rng.choice([0.0, 2.0, 40.0]), "start")])
    count_bids, count_offers = len(bid_rows), len(offer_rows)
    arrays = (numpy.ones(3, dtype=numpy.uint8), numpy.ones(3), numpy.ones(3), numpy.ones(3), numpy.ones(3), numpy.array(asks),
              numpy.zeros(count_offers), numpy.zeros(count_offers), numpy.arange(count_offers), numpy.zeros(count_bids),
              numpy.zeros(count_bids), numpy.array(pair_ptr), numpy.array(pair_offer), numpy.array(pair_bid), numpy.array(pair_quantity))
    pack = SimpleNamespace(bid_rows=numpy.array(bid_rows), offer_rows=numpy.array(offer_rows), bid_ptr=numpy.array(bid_ptr),
                           offer_ptr=numpy.array(offer_ptr))
    batch = TableBatch(arrays, pack, orders)
    results = [TableClearing.of(batch, slot, GOOD, area, MONEY) for slot, area in enumerate(("north", "south", "east"))]
    return orders, batch, results


def book_state(book):
    names = ["b1", "b2", "b3", "b4", "s1", "s2", "s3", EDGE_MINT]
    return ([book.balance(name, MONEY) for name in names],
            [[book.stock(name, GOOD, tile) for tile in TILES] for name in names],
            book.currency_table.gross_posted.tolist(), book.good_table.gross_moved.tolist())


class SettleByIdsIsSettleResults(unittest.TestCase):

    def test_random_batches_settle_as_the_key_table_path_settles_them(self):
        for seed in range(60):
            old_orders, old_batch, old_results = scenario(seed)
            new_orders, new_batch, new_results = scenario(seed)
            old = settlement_arrays.settle_results(old_orders.book, old_results, MONEY, GOOD, "sale of " + GOOD, frozenset(["b2"]),
                                                   frozenset(["s2"]))
            new = settle_by_ids(new_orders.book, new_batch, numpy.arange(3), MONEY, GOOD, "sale of " + GOOD, frozenset(["b2"]),
                                frozenset(["s2"]))
            names, tiles = new_orders.book.agent_ids.name_list, new_orders.book.tile_ids.name_list
            for market, settled in enumerate(old):
                first, last = new.agent_offset[market], new.agent_offset[market + 1]
                first_key, last_key = new.key_offset[market], new.key_offset[market + 1]
                self.assertEqual([names[each] for each in new.agent[first:last]], settled.agents, seed)
                self.assertEqual([(names[holder], tiles[tile]) for holder, tile in zip(new.key_holder[first_key:last_key],
                                                                                       new.key_tile[first_key:last_key])], settled.keys, seed)
                for column in ("paid", "received", "goods_in", "goods_out", "buyer_net", "got_goods", "paid_as_buyer", "imports", "exports"):
                    self.assertEqual(getattr(new, column)[first:last].tolist(), getattr(settled, column), (seed, column))
                self.assertEqual(new.key_to_mint[first_key:last_key].tolist(), settled.key_to_mint, seed)
                self.assertEqual(float(new.delivered[market]), settled.delivered, seed)
            self.assertEqual(book_state(new_orders.book), book_state(old_orders.book), seed)


class NumberingHelpers(unittest.TestCase):

    def test_local_numbering_of_one_market_lists_every_key_and_agent_of_the_batch(self):
        answer = local_numbering(numpy.array([2]), numpy.array([0, 1]), numpy.array([2, 2]), numpy.array([0, 1, 2]), 3)
        self.assertEqual((answer[1].tolist(), answer[2].tolist(), answer[5].tolist(), answer[6].tolist()), ([0, 3], [0, 3], [0, 1, 2], [0, 1, 2]))

    def test_local_numbering_of_two_markets_lists_the_keys_each_uses_in_batch_order(self):
        # market 0 pays key 2 to key 0; market 1 pays key 1 to key 2; keys 0, 1 are agent 0 and key 2 is agent 1
        answer = local_numbering(numpy.array([1, 1]), numpy.array([2, 1]), numpy.array([0, 2]), numpy.array([0, 0, 1]), 2)
        pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent = answer
        self.assertEqual((key_offset.tolist(), key_global.tolist(), buyer_key.tolist(), seller_key.tolist()),
                         ([0, 2, 4], [0, 2, 1, 2], [1, 0], [0, 1]))
        self.assertEqual((agent_offset.tolist(), agent_global.tolist(), key_agent.tolist()), ([0, 2, 4], [0, 1, 0, 1], [0, 1, 0, 1]))


if __name__ == "__main__":
    unittest.main()
