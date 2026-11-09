"""Column helpers the goods phase of the year calls once per good, each compared with the numpy calls it replaced. Each test calls one
function on inputs written out."""

QUICK_TOPIC = True

import unittest

import numpy

from sim.book import Book
from sim.economy.few_ids import in_ids
from sim.economy.goods_order_book import GoodsOrderBook
from sim.economy.goods_respend_unpack import paid_and_received, summed
from sim.economy.market_tables import MarketTables


def summed_by_unique(keys, values):
    distinct, inverse = numpy.unique(keys, return_inverse=True)
    return distinct, numpy.bincount(inverse, weights=values, minlength=len(distinct))


class InIdsAnswersAsIsinDoes(unittest.TestCase):

    def test_a_few_ids(self):
        values = numpy.array([4, 9, 4, 0, 7], dtype=numpy.int64)
        self.assertEqual(in_ids(values, [4, 7]).tolist(), numpy.isin(values, [4, 7]).tolist())

    def test_no_ids(self):
        values = numpy.array([4, 9], dtype=numpy.int64)
        self.assertEqual(in_ids(values, []).tolist(), [False, False])

    def test_many_ids(self):
        values = numpy.arange(30, dtype=numpy.int64)
        ids = list(range(0, 30, 3))
        self.assertEqual(in_ids(values, ids).tolist(), numpy.isin(values, ids).tolist())


class SummedAddsInTheOrderGiven(unittest.TestCase):

    def test_small_keys_give_the_sums_the_unique_route_gives(self):
        keys = numpy.array([5, 2, 5, 9, 2, 5], dtype=numpy.int64)
        values = numpy.array([0.1, 0.2, 0.3, 0.4, 0.5, 1e-17])
        got, expected = summed(keys, values), summed_by_unique(keys, values)
        self.assertEqual((got[0].tolist(), got[1].tolist()), (expected[0].tolist(), expected[1].tolist()))

    def test_keys_far_above_the_row_count_give_the_same_answer(self):
        keys = numpy.array([10 ** 9, 3, 10 ** 9], dtype=numpy.int64)
        values = numpy.array([1.5, 2.5, 4.0])
        got = summed(keys, values)
        self.assertEqual((got[0].tolist(), got[1].tolist()), ([3, 10 ** 9], [2.5, 5.5]))

    def test_no_rows(self):
        got = summed(numpy.zeros(0, dtype=numpy.int64), numpy.zeros(0))
        self.assertEqual((len(got[0]), len(got[1])), (0, 0))


class PaidAndReceivedListsEveryAgentOnce(unittest.TestCase):

    def test_matches_the_unique_and_searchsorted_route(self):
        buyers = numpy.array([3, 1, 3, 4], dtype=numpy.int64)
        sellers = numpy.array([0, 0, 4, 1], dtype=numpy.int64)
        money = numpy.array([0.1, 0.7, 0.2, 1e-17])
        people = numpy.unique(numpy.concatenate((buyers, sellers)))
        paid = numpy.bincount(numpy.searchsorted(people, buyers), weights=money, minlength=len(people))
        received = numpy.bincount(numpy.searchsorted(people, sellers), weights=money, minlength=len(people))
        got = paid_and_received(buyers, sellers, money, 6)
        self.assertEqual([each.tolist() for each in got], [people.tolist(), paid.tolist(), received.tolist()])


class MarketsByAreaNameSortsByTheAreasName(unittest.TestCase):

    def test_places_in_area_name_order(self):
        tables = MarketTables()
        orders = GoodsOrderBook(Book(), tables)
        markets = orders.market_ids(["wheat", "wheat", "wheat"], ["south", "east", "north"])
        order = orders.markets_by_area_name(numpy.array(markets, dtype=numpy.int64))
        self.assertEqual(order.tolist(), [1, 2, 0])

    def test_areas_named_after_the_ranks_were_made_are_placed_too(self):
        orders = GoodsOrderBook(Book(), MarketTables())
        first = orders.market_ids(["wheat"], ["south"])
        self.assertEqual(orders.markets_by_area_name(numpy.array(first, dtype=numpy.int64)).tolist(), [0])
        both = orders.market_ids(["wheat", "wheat"], ["south", "alpha"])
        self.assertEqual(orders.markets_by_area_name(numpy.array(both, dtype=numpy.int64)).tolist(), [1, 0])


if __name__ == "__main__":
    unittest.main()
