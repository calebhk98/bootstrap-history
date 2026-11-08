"""`year_bids.YearBids`: the year's bids of all markets as one table against the per-market columns it replaces, and its many-question
demand (`year_bids_kernels`) against the single-market `bid_columns` call, bit for bit on random bids (under numba and ROME_NO_JIT=1)."""
QUICK_TOPIC = True

import random
import types
import unittest

import numpy

from sim.economy import bid_columns, year_bids
from sim.economy.goods_added_bids import AddedBids
from sim.economy.types import Bid
from sim.tests.test_bid_columns import random_bids

FIGURES = ("floor_quantity", "flexible_quantity", "reference_price", "elasticity", "budget", "maximum_price")


def object_market(bids, added=None):
    return types.SimpleNamespace(rows=None, bids=bids, added=added)


def table_market(table, rows, added=None):
    orders = types.SimpleNamespace(tables=lambda: (table,))
    return types.SimpleNamespace(rows=types.SimpleNamespace(bid_array=numpy.array(rows, dtype=numpy.int64), orders=orders), bids=None,
                                 added=added)


def random_added(rng, good, area, count):
    return AddedBids(good, area, ["h%d" % each for each in range(count)], ["t"] * count, [rng.uniform(0.0, 9.0) for _each in range(count)],
                     [rng.uniform(0.1, 4.0) for _each in range(count)], [rng.choice([0.5, 1.0]) for _each in range(count)],
                     [rng.uniform(1.0, 90.0) for _each in range(count)], [rng.choice([float("inf"), rng.uniform(0.5, 5.0)]) for _each in range(count)])


def random_table(rng, count):
    bids = random_bids(rng, count)
    return bids, types.SimpleNamespace(**{name: numpy.array([getattr(bid, name) for bid in bids], dtype=numpy.float64) for name in FIGURES})


def columns_as_lists(columns):
    return [each.tolist() for each in columns]


class TheBlockIsEachMarketsColumnsInOrder(unittest.TestCase):

    def test_object_and_table_markets_with_added_bids_follow_first_round_then_added(self):
        for seed in range(30):
            rng = random.Random(seed)
            all_bids, table = random_table(rng, 30)
            markets, expected = {}, {}
            for number, area in enumerate(["north", "east", "south", "west", "far"]):
                key = ("bread", area) if number % 2 else ("cloth", area)
                added = random_added(rng, key[0], area, rng.randint(0, 3)) if rng.random() < 0.6 else None
                if number % 2:
                    rows = rng.sample(range(30), rng.randint(0, 6))
                    markets[key] = table_market(table, rows, added)
                    first = [all_bids[row] for row in rows]
                else:
                    first = random_bids(rng, rng.randint(0, 5))
                    markets[key] = object_market(first, added)
                expected[key] = bid_columns.columns_of_bids(first + (added.bids() if added is not None else []))
            block = year_bids.build(markets)
            self.assertEqual(block.markets, sorted(markets), seed)
            for key, columns in expected.items():
                place = block.index[key]
                self.assertEqual(columns_as_lists(block.columns_at(place)), columns_as_lists(columns), (seed, key))
                self.assertEqual(block.count(place), len(columns.floor), (seed, key))

    def test_no_markets_make_an_empty_block(self):
        block = year_bids.build({})
        self.assertEqual((len(block), block.start.tolist(), len(block.columns.floor)), (0, [0], 0))

    def test_a_mapping_of_bids_gives_the_same_block_in_sorted_order(self):
        rng = random.Random(4)
        mapping = {("b", "z"): random_bids(rng, 3), ("a", "y"): random_bids(rng, 0), ("a", "x"): random_bids(rng, 2)}
        block = year_bids.of(mapping)
        self.assertEqual(block.markets, [("a", "x"), ("a", "y"), ("b", "z")])
        self.assertEqual([block.count(place) for place in range(3)], [2, 0, 3])
        self.assertIs(year_bids.of(block), block)


class StandingBidsJoinTheirMarkets(unittest.TestCase):

    def test_with_standing_puts_them_after_the_markets_other_bids_and_adds_a_market_only_they_name(self):
        rng = random.Random(8)
        mapping = {("a", "x"): random_bids(rng, 2), ("c", "z"): random_bids(rng, 3)}
        extra, only = random_bids(rng, 2), random_bids(rng, 1)
        block = year_bids.of(mapping).with_standing({("c", "z"): extra, ("b", "y"): only})
        self.assertEqual(block.markets, [("a", "x"), ("b", "y"), ("c", "z")])
        for key, bids in (("a", "x"), mapping[("a", "x")]), (("b", "y"), only), (("c", "z"), mapping[("c", "z")] + extra):
            self.assertEqual(columns_as_lists(block.columns_at(block.index[key])), columns_as_lists(bid_columns.columns_of_bids(bids)))

    def test_no_standing_bids_leave_the_block(self):
        block = year_bids.of({("a", "x"): []})
        self.assertIs(block.with_standing({}), block)


class ManyQuestionsAreTheSingleMarketCalls(unittest.TestCase):

    def test_demand_at_many_equals_the_single_market_sum(self):
        for seed in range(40):
            rng = random.Random(seed)
            mapping = {("g", "m%d" % each): random_bids(rng, rng.randint(0, 8)) for each in range(6)}
            block = year_bids.of(mapping)
            places = [rng.randrange(6) for _each in range(20)]
            prices = [rng.uniform(0.05, 8.0) for _each in places]
            nows = [rng.choice([price, rng.uniform(0.05, 8.0)]) for price in prices]
            demand = block.demand_at_many(places, prices, nows).tolist()
            for question, place in enumerate(places):
                columns = bid_columns.columns_of_bids(mapping[block.markets[place]])
                self.assertEqual(demand[question], bid_columns.demand_at(columns, prices[question], nows[question]), (seed, question))

    def test_no_questions_and_a_place_outside_the_block_answer_nothing(self):
        block = year_bids.of({("g", "m"): [Bid("b", "g", "m", "t", 1.0, 0.0, 1.0, 1.0, 9.0, 0)]})
        self.assertEqual(block.demand_at_many([], [], []).tolist(), [])
        self.assertEqual(block.demand_at_many([5, -1], [1.0, 1.0], [1.0, 1.0]).tolist(), [0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
