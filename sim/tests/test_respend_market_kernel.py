"""The respend kernel's small market rules, each against the rule it restates: `wants_at` is `total_wanted` and keeps
each bid's quantity, `wanted_adding_untraded` is `wanted_adding` of a round that traded nothing (from quantities
`units_at_quote` makes, which are `quantity_of` at the quote), `same_ask` and `asks_unchanged` treat a NaN as equal to a NaN.
Each test writes out the inputs and calls the one function."""

QUICK_TOPIC = True

import unittest

import numpy

from sim.economy import goods_market_kernels, goods_respend_kernel, goods_respend_market_kernel as market_kernel

BIDS = dict(
    floors=numpy.zeros(4), flexibles=numpy.array([3.0, 1.0, 5.0, 2.0]), budgets=numpy.array([30.0, 0.0, 12.0, 7.0]),
    references=numpy.array([2.0, 2.0, 1.5, 3.0]), exponents=numpy.array([-1.0, -0.5, -2.0, 0.0]),
    maximums=numpy.array([numpy.inf, numpy.inf, 4.0, numpy.inf]))
ADDING = numpy.array([True, False, True, False])


class WantsAtIsTotalWanted(unittest.TestCase):

    def test_sum_and_quantities(self):
        wants = numpy.zeros(4)
        total = market_kernel.wants_at(2.5, BIDS["floors"], BIDS["flexibles"], BIDS["budgets"], BIDS["references"],
                                       BIDS["exponents"], BIDS["maximums"], True, wants)
        expected = goods_market_kernels.total_wanted(2.5, BIDS["floors"], BIDS["flexibles"], BIDS["budgets"],
                                                     BIDS["references"], BIDS["exponents"], BIDS["maximums"], True)
        self.assertEqual(total, expected)
        self.assertEqual(wants.sum(), total)


class UntradedWantedAddingIsWantedAdding(unittest.TestCase):

    def check(self, price, adding):
        arguments = (BIDS["floors"], BIDS["flexibles"], BIDS["budgets"], BIDS["references"], BIDS["exponents"],
                     BIDS["maximums"])
        expected = market_kernel.wanted_adding(price, adding, 1.0, 0.0, False, *arguments)
        quote = market_kernel.quote_of(price, BIDS["maximums"], BIDS["budgets"])
        units = numpy.zeros(4)
        if quote == quote:
            market_kernel.units_at_quote(quote, numpy.nan, numpy.zeros(4), *arguments, units)
        self.assertEqual(market_kernel.wanted_adding_untraded(quote, units, adding, 1.0), expected)

    def test_some_adding(self):
        self.check(2.5, ADDING)

    def test_all_adding(self):
        self.check(2.5, numpy.ones(4, dtype=numpy.bool_))

    def test_no_ask_quotes_the_best_ceiling(self):
        self.check(numpy.nan, ADDING)


class UnitsAtQuoteReuseTheFirstWants(unittest.TestCase):

    def test_equal_price_takes_first_wants_and_zero_for_no_budget(self):
        wants = numpy.array([1.0, 2.0, 3.0, 4.0])
        units = numpy.zeros(4)
        market_kernel.units_at_quote(2.0, 2.0, wants, BIDS["floors"], BIDS["flexibles"], BIDS["budgets"],
                                     BIDS["references"], BIDS["exponents"], BIDS["maximums"], units)
        self.assertEqual(units.tolist(), [1.0, 0.0, 3.0, 4.0])


class AsksCompare(unittest.TestCase):

    def test_same_ask(self):
        self.assertTrue(goods_respend_kernel.same_ask(numpy.nan, numpy.nan))
        self.assertTrue(goods_respend_kernel.same_ask(1.5, 1.5))
        self.assertFalse(goods_respend_kernel.same_ask(1.5, numpy.nan))

    def test_asks_unchanged(self):
        before = numpy.array([1.0, numpy.nan, 3.0])
        self.assertTrue(goods_respend_kernel.asks_unchanged(True, before, before.copy()))
        self.assertFalse(goods_respend_kernel.asks_unchanged(False, before, before.copy()))
        self.assertFalse(goods_respend_kernel.asks_unchanged(True, before, numpy.array([1.0, 2.0, 3.0])))


if __name__ == "__main__":
    unittest.main()
