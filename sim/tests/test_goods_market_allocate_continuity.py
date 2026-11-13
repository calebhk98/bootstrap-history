"""The logit allocation (goods_market_kernels.allocate_arrays) answers a small change of an input with a small change of the
answer: a seller holding next to no stock changes nothing, whatever its ask, and what a seller short of stock could not serve
is sent on in the buyers' choice shares. Each test calls the allocation once per market it compares."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.economy.goods_market_kernels import allocate_arrays


def allocate(asks, quantities, flexibles, budgets, exponent=-2.0):
    """allocate_arrays of buyers with no floor, one reference price of 1.0 and no ceiling, in one tier."""
    bids = len(flexibles)
    taken, cost, sold, requested, _flow = allocate_arrays(
        numpy.array(asks, dtype=float), numpy.array(quantities, dtype=float), numpy.zeros(bids), numpy.array(flexibles, dtype=float),
        numpy.array(budgets, dtype=float), numpy.ones(bids), numpy.full(bids, exponent), numpy.full(bids, numpy.inf), False,
        numpy.array([0, bids], dtype=numpy.int64))
    return taken, cost, sold, requested


def relative(one, other):
    return abs(one - other) / max(abs(one), abs(other), 1e-300)


class AllocationIsContinuousInStock(unittest.TestCase):
    ASKS = [1.0, 1.0, 1.0, 1.1, 1.1]
    STOCK = [60.0, 0.0, 25.0, 40.0, 1000.0]
    FLEXIBLE = [100.0, 30.0]
    BUDGET = [900.0, 200.0]

    def with_stock(self, dust):
        stock = list(self.STOCK)
        stock[1] = dust
        return allocate(self.ASKS, stock, self.FLEXIBLE, self.BUDGET)

    def without_seller(self):
        keep = [0, 2, 3, 4]
        return allocate([self.ASKS[i] for i in keep], [self.STOCK[i] for i in keep], self.FLEXIBLE, self.BUDGET)

    def test_a_seller_with_dust_stock_trades_what_the_market_without_it_trades(self):
        taken, _cost, _sold, _requested = self.with_stock(2.9e-11)
        taken_without, _cost, _sold, _requested = self.without_seller()
        for bid in range(2):
            self.assertLess(relative(taken[bid], taken_without[bid]), 1e-9)

    def test_a_seller_with_dust_stock_leaves_the_demand_asked_unchanged(self):
        _taken, _cost, _sold, requested = self.with_stock(2.9e-11)
        _taken, _cost, _sold, requested_without = self.without_seller()
        self.assertLess(relative(requested, requested_without), 1e-9)

    def test_the_answer_moves_in_proportion_to_the_stock(self):
        _taken, _cost, _sold, requested_without = self.without_seller()
        gaps = []
        for stock in (1e-4, 1e-2):
            taken, _cost, _sold, requested = self.with_stock(stock)
            gaps.append(relative(requested, requested_without))
        self.assertLessEqual(gaps[0], 0.1 * gaps[1] + 1e-12)       # a hundredth of the stock moves it by about a hundredth as far


if __name__ == "__main__":
    unittest.main()
