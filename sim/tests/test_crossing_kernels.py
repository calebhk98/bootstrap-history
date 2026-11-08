"""The price search over columns against the Python it replaces, bit for bit, on written-out and random markets (under numba and
ROME_NO_JIT=1): the quantities wanted (`DemandSchedule.total_at`, `uncapped_at`), the crossing price of `goods_market.crossing` for books
of several levels, the price at which a producer's added output sells (`expansion_price.price_with_supply`) and the clearing order of a
market's bids. The reference is the Python search: the kernel entry of `goods_market.crossing` is switched off for it."""
QUICK_TOPIC = True

import math
import random
import unittest
from types import SimpleNamespace
from unittest import mock

import numpy

from sim.economy import bid_columns, bid_order, crossing_columns, crossing_demand, expansion_price, goods_market
from sim.economy.types import Bid, Offer


def random_bids(rng, count, ceilings=True, distinct=3):
    """Bids with ties in priority, buyer and tile, no-budget and floor-only bids, and a few distinct schedules."""
    bids = []
    for _each in range(count):
        flexible = rng.choice([0.0, rng.uniform(0.1, 40.0)])
        bids.append(Bid("b%d" % rng.randint(0, count), "g", "a", "t%d" % rng.randint(0, 2), rng.choice([0.0, rng.uniform(0.0, 20.0)]), flexible,
                        rng.choice([0.0, 1.0, 2.0, 0.5 + rng.randint(0, distinct)]), rng.choice([0.0, 0.5, 1.0, 2.0, 3.0]),
                        rng.choice([0.0, rng.uniform(1.0, 80.0), rng.uniform(80.0, 900.0), math.inf, 1e9]), rng.randint(0, 2),
                        maximum_price=rng.choice([math.inf, math.inf, rng.uniform(0.2, 6.0)]) if ceilings else math.inf))
    return bids


def python_search(function, *arguments):
    """`function` with the crossing's kernel entry off, so the Python search answers."""
    with mock.patch.object(goods_market, "_kernel_price", lambda *rest: None):
        return function(*arguments)


def outcome(function, *arguments):
    """What `function` answers, or the type of the error it raises (the Python raises where a power or exponential overflows)."""
    try:
        return function(*arguments)
    except (OverflowError, ZeroDivisionError, ValueError) as error:
        return type(error)


def prepared(bids):
    ordered = sorted(bids, key=lambda bid: (bid.priority, bid.buyer, bid.tile))
    return ordered, crossing_columns.demand_columns(bid_columns.columns_of_bids(ordered), numpy.arange(len(ordered), dtype=numpy.int64))


class QuantitiesWantedAreTheSchedulesBitForBit(unittest.TestCase):

    def test_total_and_uncapped_at_random_prices(self):
        for seed in range(80):
            rng = random.Random(seed)
            bids = random_bids(rng, rng.randint(1, 14), ceilings=seed % 2 == 0)
            _ordered, demand = prepared(bids)
            schedule = goods_market.Buyers(bids, None).schedule
            for price in [0.0, -1.0, 1e-9, 1.0, 2.5, 7.0, 40.0, rng.uniform(0.01, 90.0), rng.uniform(0.01, 5.0)]:
                flags = numpy.zeros(1, dtype=numpy.int64)
                self.assertEqual(crossing_demand.total_at(price, demand, flags), schedule.total_at(price), (seed, price))
                if price > 0.0:
                    self.assertEqual(crossing_demand.uncapped_at(price, demand, flags), schedule.uncapped_at(price), (seed, price))
                self.assertEqual(flags[0], 0)

    def test_a_written_out_market(self):
        bids = [Bid("a", "g", "x", "t", 2.0, 10.0, 1.0, 1.0, 100.0), Bid("b", "g", "x", "t", 1.0, 0.0, 0.0, 0.0, 5.0),
                Bid("c", "g", "x", "t", 0.0, 6.0, 1.0, 1.0, 0.0), Bid("d", "g", "x", "t", 0.0, 3.0, 2.0, 2.0, 50.0, maximum_price=1.5)]
        _ordered, demand = prepared(bids)
        flags = numpy.zeros(1, dtype=numpy.int64)
        self.assertEqual(demand.group_start.tolist(), [0, 1, 2, 3])      # groups: (1, 1), constant, (2, 2); the no-budget bid has no row
        for price in (0.5, 1.0, 2.0):
            self.assertEqual(crossing_demand.total_at(price, demand, flags), math.fsum(goods_market.quantity_at(bid, price) for bid in bids))

    def test_a_nan_or_an_infinite_floor_is_not_prepared(self):
        for value in (math.nan, math.inf):
            bids = [Bid("a", "g", "x", "t", value, 1.0, 1.0, 1.0, 10.0)]
            self.assertIsNone(prepared(bids)[1])


class CrossingPriceIsTheSearchBitForBit(unittest.TestCase):

    def book(self, rng, good="g"):
        return [Offer("s%d" % each, good, "a", "t", rng.uniform(0.1, 60.0), rng.choice([0.0, 0.0, rng.uniform(0.2, 8.0), 3.0]))
                for each in range(rng.randint(1, 5))]

    def test_several_levels_against_the_python_search(self):
        for seed in range(150):
            rng = random.Random(seed)
            bids = random_bids(rng, rng.randint(1, 16), ceilings=seed % 3 != 0, distinct=1 + seed % 4)
            offers = goods_market.in_clearing_order(self.book(rng))
            last = rng.choice([None, rng.uniform(0.2, 5.0)])
            kernel = outcome(goods_market.crossing, goods_market.Buyers(bids, last), offers)
            python = outcome(python_search, goods_market.crossing, goods_market.Buyers(bids, last), offers)
            if isinstance(python, type):
                self.assertIs(kernel, python, seed)
                continue
            self.assertEqual(kernel[0], python[0], seed)
            self.assertEqual(kernel[2], python[2], seed)
            self.assertEqual(None if kernel[3] is None else list(kernel[3]), None if python[3] is None else list(python[3]), seed)

    def test_many_schedules_use_the_cheap_pass_and_still_agree(self):
        for seed in range(30):
            rng = random.Random(1000 + seed)
            bids = [Bid("b%d" % each, "g", "a", "t", rng.uniform(0.0, 2.0), rng.uniform(1.0, 30.0), 1.0 + rng.randint(0, 1), 1.0 + rng.randint(0, 1),
                        rng.uniform(5.0, 400.0), 0) for each in range(120)]
            offers = goods_market.in_clearing_order(self.book(rng))
            self.assertEqual(goods_market.crossing(goods_market.Buyers(bids, None), offers)[0],
                             python_search(goods_market.crossing, goods_market.Buyers(bids, None), offers)[0], seed)

    def test_an_overflowing_power_runs_the_python_instead(self):
        bids = [Bid("a", "g", "x", "t", 0.0, 1e300, 1e-300, 400.0, 1e308)]
        offers = [Offer("s", "g", "x", "t", 5.0, 1.0)]
        outcomes = []
        for run in (goods_market.crossing, lambda *arguments: python_search(goods_market.crossing, *arguments)):
            try:
                outcomes.append(run(goods_market.Buyers(bids, None), goods_market.in_clearing_order(offers))[0])
            except (OverflowError, ZeroDivisionError, ValueError) as error:
                outcomes.append(type(error))
        self.assertEqual(outcomes[0], outcomes[1])


class ExpansionPriceFromColumns(unittest.TestCase):

    def test_prepared_market_equals_the_python_price(self):
        for seed in range(120):
            rng = random.Random(seed)
            bids = random_bids(rng, rng.randint(1, 16), ceilings=seed % 2 == 0, distinct=1 + seed % 4)
            market = expansion_price.PreparedMarket(bids)
            for quantity in (0.0, 1e-12, 0.5, 7.0, 55.0, rng.uniform(1.0, 400.0), 1e5):
                expected = outcome(python_search, expansion_price.price_with_supply, bids, "g", "a", quantity)
                self.assertEqual(outcome(market.price_with_supply, "g", "a", quantity), expected, (seed, quantity))

    def test_market_bids_in_their_own_order_give_the_same_price(self):
        rng = random.Random(7)
        bids = random_bids(rng, 12)
        market_bids = bid_columns.MarketBids(lambda: bid_columns.columns_of_bids(bids), lambda: list(bids), len(bids))
        for quantity in (3.0, 30.0, 90.0):
            self.assertEqual(expansion_price.PreparedMarket(market_bids).price_with_supply("g", "a", quantity),
                             python_search(expansion_price.price_with_supply, bids, "g", "a", quantity))

    def test_buyers_with_no_price_scale_show_no_price(self):
        floor_only = [Bid("buyer", "g", "a", "t", 5.0, 0.0, 0.0, 1.0, 100.0)]
        self.assertIsNone(expansion_price.PreparedMarket(floor_only).price_with_supply("g", "a", 3.0))

    def test_a_column_market_that_cannot_be_prepared_falls_back_to_objects(self):
        bids = [Bid("a", "g", "x", "t", 4.0, math.inf, 1.0, 1.0, 100.0)]
        market = expansion_price.PreparedMarket(bids)
        self.assertEqual(market.price_with_supply("g", "x", 2.0), python_search(expansion_price.price_with_supply, bids, "g", "x", 2.0))


class ClearingOrder(unittest.TestCase):

    def test_order_of_bids_is_the_stable_sort_buyers_use(self):
        for seed in range(40):
            bids = random_bids(random.Random(seed), 15)
            order = bid_columns.order_of_bids(bids)
            self.assertEqual([bids[place] for place in order], goods_market.Buyers(bids, None).bids)

    def test_order_from_table_rows_and_added_bids_is_the_same_permutation(self):
        rng = random.Random(4)
        bids = random_bids(rng, 9)
        added = random_bids(rng, 4)
        agents = sorted({bid.buyer for bid in bids + added})
        tiles = ["t0", "t1", "t2"]
        table = SimpleNamespace(buyer=numpy.array([agents.index(bid.buyer) for bid in bids]),
                                tile=numpy.array([tiles.index(bid.tile) for bid in bids]),
                                priority=numpy.array([bid.priority for bid in bids]))
        book = SimpleNamespace(agent_ids=SimpleNamespace(name_list=agents), tile_ids=SimpleNamespace(name_list=tiles))
        rows = SimpleNamespace(orders=SimpleNamespace(tables=lambda: (table, None), book=book), bid_array=numpy.arange(len(bids)))
        extra = type("Added", (), {"buyer": [bid.buyer for bid in added], "tile": [bid.tile for bid in added],
                                   "__len__": lambda self: len(self.buyer)})()
        everything = bids + [Bid(bid.buyer, "g", "a", bid.tile, 0.0, 1.0, 1.0, 1.0, 1.0, 1) for bid in added]
        self.assertEqual(bid_order.clearing_order(rows, extra).tolist(), bid_columns.order_of_bids(everything).tolist())


if __name__ == "__main__":
    unittest.main()
