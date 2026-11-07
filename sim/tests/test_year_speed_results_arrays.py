"""Numba port, a good's markets cleared to arrays: the clearing `goods_year_batch.clear_markets` returns for a market that traded
(`goods_year_results.ArrayClearing`) is the clearing `goods_market.clear` gives at the same reservations (quantity, price, what
was asked and offered, the fills and the pairing, built when read), the offers it leaves are `goods_respend.offers_left`, and a
good's results settled straight from the arrays (`settlement.settle_goods_many`) leave the book, and each market's own figures, as
the same results settled from their `Pairing` do. Random bids and offers on the random economy of year_close_fixture; no game.

A relative tolerance is needed because the kernel adds the units of a market left to right where the old path adds them with
`math.fsum`, and the settlement kernel adds each agent's pairs in the order of the arrays."""

QUICK_TOPIC = True

import random
import unittest

from sim.book import Book
from sim.economy import goods_market, goods_respend, goods_year_batch, settlement
from sim.economy.goods_market_fills import sold_by_seller_tile
from sim.economy.goods_year_results import ArrayClearing
from sim.economy.market_memory import market_key
from sim.economy.types import ClearingResult, EDGE_PRODUCTION, GoodsMove, Transfer, EDGE_MINT
from sim.economy.year_arrays import YearArrays
from sim.economy.year_arrays_costs import OfferCosts, refreshed
from sim.tests.test_year_speed_goods_markets import near, random_bid, random_offers, with_markets
from sim.tests.test_year_speed_settlement import close, snapshot
from sim.tests.year_close_fixture import AREAS, GOODS, MONEY


def batched_markets(seed):
    setup, record, view, area_map = with_markets(seed)
    rng = random.Random(500 + seed)
    memory = record.memory
    for good in GOODS:
        for area in AREAS:
            if rng.random() < 0.8:
                memory.volume_weights[market_key(good, area)] = rng.uniform(1.0, 300.0)
    arrays = refreshed(YearArrays.build(setup, record, area_map, view), setup, record, view)
    costs = OfferCosts.build(arrays, view.interest_rate(MONEY))
    markets = []
    for good in GOODS:
        if not setup.specs[good].portable:
            continue
        for area in AREAS:
            bids = [random_bid(rng, index, good, area) for index in range(rng.choice([0, 1, 3, 7, 12]))]
            offers = random_offers(rng, setup, record, good, area)
            if goods_year_batch.batchable(setup, bids, offers, good, arrays):
                markets.append((good, area, bids, offers, memory.prices.get(market_key(good, area))))
    return setup, record, view, arrays, costs, markets


def same_fills(old, new):
    return len(old) == len(new) and all(
        left.agent == right.agent and left.side == right.side and left.tile == right.tile and near(left.quantity, right.quantity)
        and near(left.price, right.price) for left, right in zip(old, new))


class ArrayClearingIsTheClearing(unittest.TestCase):

    def test_random_markets(self):
        compared = 0
        for seed in range(25):
            setup, record, view, arrays, costs, markets = batched_markets(seed)
            for (good, area, bids, _offers, last_price), (chosen, result) in zip(
                    markets, goods_year_batch.clear_markets(setup, record, view, arrays, costs, markets)):
                if not isinstance(result, ArrayClearing):
                    continue
                reference = goods_market.clear(bids, chosen, good, area, MONEY, last_price)
                self.assertTrue(near(reference.quantity, result.quantity))
                self.assertTrue(near(reference.price, result.price))
                self.assertTrue(near(reference.demand_at_price, result.demand_at_price))
                self.assertTrue(near(reference.offered_at_price, result.offered_at_price))
                self.assertTrue(same_fills(reference.fills, result.fills))
                old, new = reference.pairing, result.pairing
                self.assertEqual((old.buyers, old.sellers, old.buyer_index, old.seller_index),
                                 (new.buyers, new.sellers, new.buyer_index, new.seller_index))
                self.assertTrue(all(near(left, right) for left, right in zip(old.quantity + old.asks, new.quantity + new.asks)))
                left_old = goods_respend.offers_left(chosen, sold_by_seller_tile(reference.fills))
                left_new = result.offers_left()
                self.assertEqual(sorted((each.seller, each.tile) for each in left_old),
                                 sorted((each.seller, each.tile) for each in left_new))
                self.assertTrue(all(near(left.quantity, right.quantity) for left, right in zip(
                    sorted(left_old, key=lambda each: (each.seller, each.tile, each.quantity)),
                    sorted(left_new, key=lambda each: (each.seller, each.tile, each.quantity)))))
                self.assertEqual(sorted(sold_by_seller_tile(reference.fills)), sorted(result.sold_by_key()))
                compared += 1
        self.assertGreater(compared, 100)

    def test_a_market_that_does_not_trade_is_a_plain_result(self):
        found = 0
        for seed in range(10):
            setup, record, view, arrays, costs, markets = batched_markets(seed)
            for _chosen, result in goods_year_batch.clear_markets(setup, record, view, arrays, costs, markets):
                if not isinstance(result, ArrayClearing):
                    self.assertEqual(result.quantity, 0.0)
                    self.assertEqual(result.fills, ())
                    found += 1
        self.assertGreater(found, 5)


def funded_books(rng, setup, markets, results):
    """Two equal books where every buyer and seller of the markets holds some money and the sellers some stock (short for some)."""
    books = [Book(), Book()]
    amounts = {}
    for _good, _area, bids, offers, _last in markets:
        for bid in bids:
            amounts.setdefault(bid.buyer, rng.choice([0.0, rng.uniform(1, 200), rng.uniform(500, 8000)]))
        for offer in offers:
            amounts.setdefault(offer.seller, rng.choice([0.0, rng.uniform(1, 200), rng.uniform(500, 8000)]))
    stock = {}
    for _good, _area, bids, offers, _last in markets:
        for offer in offers:
            stock.setdefault((offer.seller, offer.tile), rng.choice([offer.quantity, offer.quantity * 0.4, offer.quantity * 3.0]))
    for book in books:
        for agent, amount in sorted(amounts.items()):
            book.transfer(Transfer(EDGE_MINT, agent, MONEY, amount, "start"))
        for (agent, tile), quantity in sorted(stock.items()):
            book.move(GoodsMove(EDGE_PRODUCTION, agent, results[0].good, tile, quantity, "start"))
    return books


class SettlingFromArraysIsSettlingFromPairings(unittest.TestCase):

    def test_random_goods(self):
        compared = 0
        for seed in range(25):
            setup, record, view, arrays, costs, markets = batched_markets(seed)
            rng = random.Random(900 + seed)
            for good in GOODS:
                these = [market for market in markets if market[0] == good]
                results = [result for _chosen, result in goods_year_batch.clear_markets(setup, record, view, arrays, costs, these)
                           ] if these else []
                traded = [result for result in results if result.quantity > 0.0]
                if not traded:
                    continue
                these = [market for market, result in zip(these, results) if result.quantity > 0.0]
                book_new, book_old = funded_books(rng, setup, these, traded)
                accounts = frozenset(rng.sample(sorted({bid.buyer for market in these for bid in market[2]}), 1)) if rng.random() < 0.5 else frozenset()
                done_new = settlement.settle_goods_many(book_new, traded, accounts, accounts)
                plain = [ClearingResult(result.good, result.area, result.currency, result.price, result.quantity,
                                        result.demand_at_price, result.offered_at_price, result.fills, None, result.pairing)
                         for result in traded]
                done_old = settlement.settle_goods_many(book_old, plain, accounts, accounts)
                close(snapshot(book_new), snapshot(book_old))
                for new, old in zip(done_new, done_old):
                    self.assertTrue(near(new.delivered, old.delivered))
                    close(dict(zip(new.agents, new.paid)), dict(zip(old.agents, old.paid)))
                    close(dict(zip(new.agents, new.received)), dict(zip(old.agents, old.received)))
                    close(dict(zip(new.agents, new.goods_in)), dict(zip(old.agents, old.goods_in)))
                    close(dict(zip(new.keys, new.key_to_mint)), dict(zip(old.keys, old.key_to_mint)))
                    compared += 1
        self.assertGreater(compared, 60)


if __name__ == "__main__":
    unittest.main()
