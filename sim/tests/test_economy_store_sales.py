"""Households sell part of a store that has grown beyond its target, or cheaply when short of food money;
a game without durables is unchanged."""

QUICK_TOPIC = True

import unittest

from sim.economy import households_store
from sim.tests import economy_fixture as fixture
from sim.tests.economy_store_view import View, metal_held, orders



def metal_offers(result):
    return [offer for offer in result.offers if offer.good == fixture.METAL]


def settled_target_kilograms():
    """The kilograms at which the store is on target, found by bidding with nothing held."""
    bid = next(bid for bid in orders().bids if bid.priority == households_store.STORE_PRIORITY)
    return bid.budget / 95.0


class StoreSaleTests(unittest.TestCase):
    def test_a_store_on_target_is_not_offered(self):
        self.assertEqual(metal_offers(orders(View(stocks=metal_held(settled_target_kilograms())))), [])

    def test_a_doubling_of_the_price_makes_holders_offer_the_excess(self):
        held = settled_target_kilograms()
        before = orders(View(stocks=metal_held(held)))
        after = orders(View(prices={fixture.METAL: 190.0}, stocks=metal_held(held)))
        self.assertEqual(metal_offers(before), [])
        offers = metal_offers(after)
        self.assertEqual(len(offers), 1)
        self.assertGreater(offers[0].quantity, 0.0)
        self.assertLess(offers[0].quantity, held)
        self.assertLessEqual(offers[0].reservation_price, 190.0)

    def test_the_excess_is_offered_at_the_holding_reservation(self):
        held = settled_target_kilograms() * 3.0
        offer = metal_offers(orders(View(stocks=metal_held(held))))[0]
        self.assertGreater(offer.reservation_price, 95.0 * households_store.STORE_LIQUIDATION_RESERVATION_SHARE)
        self.assertLess(offer.reservation_price, 95.0)

    def test_a_cash_shortfall_below_the_floor_cost_makes_them_offer_stores_cheaply(self):
        held = 200.0
        result = orders(View(stocks=metal_held(held)), cash=100.0, income=0.0)
        low = 95.0 * households_store.STORE_LIQUIDATION_RESERVATION_SHARE
        cheap = [offer for offer in metal_offers(result) if abs(offer.reservation_price - low) < 1e-9]
        self.assertEqual(len(cheap), 1)
        floor_cost = 250.0 * 100.0 * 0.3
        self.assertGreaterEqual(cheap[0].quantity * low, floor_cost - 100.0 - 1e-6)

    def test_what_is_offered_never_exceeds_what_is_held(self):
        for held in (0.01, 0.5, 2.0, 50.0):
            for cash in (0.0, 100.0, 20000.0):
                result = orders(View(stocks=metal_held(held)), cash=cash, income=0.0)
                self.assertLessEqual(sum(offer.quantity for offer in metal_offers(result)), held + 1e-9)

    def test_no_store_is_offered_without_one_held(self):
        self.assertEqual(metal_offers(orders(cash=100.0, income=0.0)), [])


class NoDurablesTests(unittest.TestCase):
    def test_without_service_lives_there_is_no_store_candidate(self):
        view = View()
        self.assertEqual(households_store.store_candidates(fixture.specs(), view.prices, 0.3), {})


if __name__ == "__main__":
    unittest.main()
