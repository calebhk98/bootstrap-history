"""Households above subsistence bid for a durable, dense good to hold as wealth."""

QUICK_TOPIC = True

import unittest

from sim.economy.households_store import STORE_PRIORITY
from sim.tests import economy_fixture as fixture
from sim.tests.economy_store_view import View, metal_held, orders


def store_bid(result):
    return next((bid for bid in result.bids if bid.good == fixture.METAL and bid.priority == STORE_PRIORITY), None)


def lent(result):
    return sum(offer.amount for offer in result.funds_offers)


class StoreBidTests(unittest.TestCase):
    def test_a_cohort_above_subsistence_bids_for_the_store(self):
        bid = store_bid(orders())
        self.assertIsNotNone(bid)
        self.assertEqual(bid.floor_quantity, 0.0)

    def test_the_store_ranks_after_the_need_tiers(self):
        result = orders()
        store = store_bid(result)
        self.assertTrue(all(bid.priority < STORE_PRIORITY for bid in result.bids if bid is not store))

    def test_total_budgets_never_exceed_cash(self):
        for cash in (50.0, 500.0, 5000.0, 20000.0, 200000.0):
            result = orders(cash=cash)
            self.assertLessEqual(sum(bid.budget for bid in result.bids) + lent(result), cash + 1e-6)

    def test_funds_offered_fall_by_the_store_bid(self):
        with_store = orders()
        bid = store_bid(with_store)
        without = orders(specs=fixture.specs())
        self.assertGreater(bid.budget, 0.0)
        self.assertAlmostEqual(lent(without) - lent(with_store), bid.budget, places=6)

    def test_nothing_is_bid_when_the_store_is_at_target(self):
        self.assertIsNone(store_bid(orders(View(stocks=metal_held(1000.0)))))

    def test_nothing_is_bid_when_cash_is_at_the_buffer(self):
        self.assertIsNone(store_bid(orders(cash=0.0)))

    def test_expected_inflation_raises_the_bid(self):
        calm = store_bid(orders(View(inflation=0.0)))
        inflating = store_bid(orders(View(inflation=0.1), expected_inflation=0.1))
        self.assertGreater(inflating.budget, calm.budget)

    def test_a_good_without_a_service_life_is_not_a_store(self):
        self.assertIsNone(store_bid(orders(specs=fixture.specs())))


if __name__ == "__main__":
    unittest.main()
