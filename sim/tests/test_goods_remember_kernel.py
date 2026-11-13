"""The memory's notes of a year's goods markets over columns (`goods_remember_kernel`) give, bit for bit, what the Python rules give on random
inputs: the price sellers got (`year_goods._received_price`'s sum), what a market's buyers would take at a price (`market_memory_asks.wanted_at`
with the added bids' `quantities_at`), the quote of a market with bids and no offers (`goods_market_rows.bids_only_quote`) and the signal."""

QUICK_TOPIC = True

import math
import random
import types
import unittest

import numpy as np

from sim.economy import goods_remember_kernel as kernel
from sim.economy.goods_added_bids import AddedBids
from sim.economy.goods_market_rows import bids_only_quote
from sim.economy.goods_market import quantity_at
from sim.economy.market_memory_asks import REPRESENTATIVE_TRADE_SHARE, RESUMED_TRADE_MEMORY_SHARE
from sim.economy.market_memory_blend import MEMORY_VOLUME_FLOOR, blended_price, reference_volume
from sim.economy.market_memory_offers import NO_OFFER_MEMORY_SHARE, THIN_TRADE_COST_SHARE
from sim.economy.types import EDGE_EXTERNAL, QUOTE_BEST_UNFILLED_BID, QUOTE_COST_COVERING, Bid


def random_bid(rng, buyer):
    ceiling = rng.choice((math.inf, rng.uniform(0.1, 30.0), 0.0))
    reference = rng.choice((0.0, rng.uniform(0.05, 20.0), 1e-300))
    return Bid(buyer, "grain", "a1", "t", rng.choice((0.0, rng.uniform(0.0, 9.0))), rng.choice((0.0, rng.uniform(0.0, 90.0))), reference,
               rng.choice((0.0, rng.uniform(0.1, 3.0), 40.0)), rng.choice((0.0, rng.uniform(1.0, 5000.0))), 0, maximum_price=ceiling)


def columns_of(bids):
    return [np.array([getattr(bid, name) for bid in bids], dtype=np.float64) for name in
            ("floor_quantity", "flexible_quantity", "reference_price", "elasticity", "budget", "maximum_price")]


class WantedTests(unittest.TestCase):
    def test_random_markets_equal_wanted_at_and_the_added_bids(self):
        rng = random.Random(3)
        markets = []
        for _each in range(120):
            bids = [random_bid(rng, rng.choice(("h1", "h2", EDGE_EXTERNAL))) for _bid in range(rng.randint(0, 6))]
            count = rng.randint(0, 3)
            added = AddedBids("grain", "a1", ["h"] * count, ["t"] * count, [rng.uniform(0.0, 50.0) for _bid in range(count)],
                              [rng.uniform(0.05, 20.0) for _bid in range(count)], [rng.uniform(0.1, 3.0) for _bid in range(count)],
                              [rng.choice((0.0, rng.uniform(1.0, 900.0))) for _bid in range(count)],
                              [rng.choice((math.inf, rng.uniform(0.1, 30.0))) for _bid in range(count)])
            markets.append((bids, added, rng.choice((None, 0.0, -1.0, rng.uniform(0.01, 40.0)))))
        bids_all = [bid for bids, _added, _price in markets for bid in bids]
        floor, flexible, reference, elasticity, budget, maximum = columns_of(bids_all)
        counted = np.array([bid.buyer != EDGE_EXTERNAL for bid in bids_all], dtype=np.bool_)
        bid_ptr = np.concatenate(([0], np.cumsum([len(bids) for bids, _added, _price in markets]))).astype(np.int64)
        added_ptr = np.concatenate(([0], np.cumsum([len(added) for _bids, added, _price in markets]))).astype(np.int64)
        pieces = [np.array(sum((getattr(added, name) for _bids, added, _price in markets), []), dtype=np.float64)
                  for name in ("flexible", "reference", "elasticity", "budget", "maximum")]
        price = np.array([math.nan if each is None else each for _bids, _added, each in markets])
        flags = np.zeros(1, dtype=np.int64)
        found = kernel.wanted_at_markets(price, bid_ptr, floor, flexible, reference, elasticity, budget, maximum, counted, added_ptr, *pieces, flags)
        self.assertEqual(flags[0], 0)       # no figure here is one the kernel leaves to the Python
        for place, (bids, added, each) in enumerate(markets):
            expected = 0.0
            if each and each > 0.0:
                expected = math.fsum([quantity_at(bid, each) for bid in bids if bid.buyer != EDGE_EXTERNAL] + added.quantities_at(each))
            self.assertEqual(found[place], expected, (place, each))


class ReceivedTests(unittest.TestCase):
    def test_the_price_sellers_got_is_the_exact_weighted_mean_of_the_rounds_that_matched(self):
        rng = random.Random(5)
        rounds = [(rng.randrange(6), rng.choice((0.0, rng.uniform(0.1, 90.0))), rng.uniform(0.5, 30.0)) for _each in range(80)]
        market = np.array([each[0] for each in rounds], dtype=np.int64)
        quantity = np.array([each[1] for each in rounds])
        price = np.array([each[2] for each in rounds])
        found = kernel.received_prices(market, quantity, price, len(rounds), 7)
        for number in range(7):
            mine = [(units, paid) for each, units, paid in rounds if each == number and units > 0.0]
            if not mine:
                self.assertTrue(math.isnan(found[number]))
                continue
            self.assertEqual(found[number], math.fsum(units * paid for units, paid in mine) / math.fsum(units for units, _paid in mine))


class BidFiguresTests(unittest.TestCase):
    def test_the_quote_of_a_market_with_bids_and_no_offers(self):
        rng = random.Random(7)
        markets = [[random_bid(rng, "h1") for _bid in range(rng.randint(0, 5))] for _each in range(100)]
        bids_all = [bid for bids in markets for bid in bids]
        budget, maximum = [np.array([getattr(bid, name) for bid in bids_all]) for name in ("budget", "maximum_price")]
        pointers = np.concatenate(([0], np.cumsum([len(bids) for bids in markets]))).astype(np.int64)
        funded, best = kernel.bid_figures(pointers, budget, maximum)
        lists = types.SimpleNamespace(budget=[bid.budget for bid in bids_all], maximum_price=[bid.maximum_price for bid in bids_all])
        for place, bids in enumerate(markets):
            rows = range(int(pointers[place]), int(pointers[place + 1]))
            for cost in (None, 2.5):
                quote = bids_only_quote(lists, rows, cost)
                if cost is not None and funded[place]:
                    self.assertEqual(quote.kind, QUOTE_COST_COVERING)
                elif quote is not None:
                    self.assertEqual((quote.kind, quote.price), (QUOTE_BEST_UNFILLED_BID, best[place]))
                else:
                    self.assertTrue(math.isnan(best[place]))


class SignalTests(unittest.TestCase):
    def test_random_markets_equal_the_rules(self):
        rng = random.Random(11)
        count = 300
        none = math.nan
        old = np.array([rng.choice((none, rng.uniform(0.2, 30.0))) for _each in range(count)])
        was_quote = np.array([rng.random() < 0.4 for _each in range(count)])
        usual = np.array([rng.choice((0.0, 0.0, rng.uniform(0.5, 80.0))) for _each in range(count)])
        quiet = np.array([rng.choice((0, 0, 1, 3)) for _each in range(count)], dtype=np.int64)
        total = np.array([rng.choice((0.0, 2.5e-16, rng.uniform(0.01, 90.0))) for _each in range(count)])
        received = np.array([rng.choice((none, rng.uniform(0.2, 30.0))) for _each in range(count)])
        wanted = np.array([rng.choice((0.0, 1e-16, rng.uniform(0.0, 120.0))) for _each in range(count)])
        scale = np.array([rng.choice((0.0, rng.uniform(0.5, 80.0))) for _each in range(count)])
        quote_price = np.array([rng.choice((none, rng.uniform(0.2, 30.0))) for _each in range(count)])
        quote_kind = np.where(np.isnan(quote_price), 0, 1).astype(np.int64)
        has_bids = np.array([rng.random() < 0.6 for _each in range(count)])
        offers_left = np.array([rng.choice((0, 0, 2)) for _each in range(count)], dtype=np.int64)
        cost = np.array([rng.choice((none, 0.0, rng.uniform(0.2, 30.0))) for _each in range(count)])
        funded = np.array([rng.random() < 0.6 for _each in range(count)])
        best = np.array([rng.choice((none, rng.uniform(0.2, 30.0))) for _each in range(count)])
        signal, kind, from_trade = kernel.signals(old, was_quote, usual, scale, quiet, total, received, wanted, quote_price, quote_kind, has_bids,
                                                  offers_left, cost, funded, best, REPRESENTATIVE_TRADE_SHARE, RESUMED_TRADE_MEMORY_SHARE,
                                                  NO_OFFER_MEMORY_SHARE, THIN_TRADE_COST_SHARE, MEMORY_VOLUME_FLOOR)
        for place in range(count):
            previous = None if math.isnan(old[place]) else float(old[place])
            traded = total[place] > 0.0 and not math.isnan(received[place])
            self.assertEqual(from_trade[place], traded)
            price = None if math.isnan(quote_price[place]) else float(quote_price[place])
            if has_bids[place] and offers_left[place] == 0:
                if not math.isnan(cost[place]) and cost[place] > 0.0 and funded[place]:
                    price = float(cost[place])
                else:
                    price = None if math.isnan(best[place]) else float(best[place])
            made = None if math.isnan(cost[place]) or cost[place] <= 0.0 else float(cost[place])
            if price is None and made is not None:     # nothing to quote: the making cost
                price = made
            reference = reference_volume(float(usual[place]), float(wanted[place]), float(scale[place]), REPRESENTATIVE_TRADE_SHARE)
            expected = blended_price(previous, bool(was_quote[place]), int(quiet[place]), reference, float(total[place]) if traded else 0.0,
                                     float(received[place]) if traded else None, float(wanted[place]), offers_left[place] == 0, price, made)
            self.assertEqual(None if math.isnan(signal[place]) else signal[place], expected, place)
            self.assertEqual(kind[place] != 0, price is not None and not traded)
