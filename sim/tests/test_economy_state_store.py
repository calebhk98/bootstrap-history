"""A state keeps part of the cash it does not spend in the durable stores households use, by the same rule: the rule
(`state_store.orders`) is called on a stand-in setup, record and market view written out here."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import state_store
from sim.tests import economy_fixture as fixture
from sim.tests.economy_store_view import BASKET, SPECS, View

STATE = "state:fixture"


class Book:
    def __init__(self, cash):
        self.cash = cash

    def balance(self, agent, currency):
        return self.cash


def setup_with(specs):
    return types.SimpleNamespace(state_agent=STATE, capital_tile=fixture.TOWN, currency_id="coin", specs=specs,
                                 basket_for=lambda tile: BASKET)


def record_with(unplanned_cash, cash=None, deficit=0.0):
    budget = types.SimpleNamespace(expected_inflation=0.0, unplanned_cash=unplanned_cash, deficit=deficit)
    return types.SimpleNamespace(state_budget=budget, book=Book(unplanned_cash if cash is None else cash))


def metal_stock(kilograms):
    return {(STATE, fixture.METAL, fixture.TOWN): kilograms}


class StateStoreTests(unittest.TestCase):
    def test_a_state_with_cash_beyond_its_plan_bids_for_a_durable_store(self):
        bids, offers, kept = state_store.orders(setup_with(SPECS), record_with(1.0e6), View())
        self.assertEqual([bid.good for bid in bids], [fixture.METAL])
        self.assertGreater(bids[0].budget, 0.0)
        self.assertEqual((offers, kept), ([], {}))

    def test_a_state_holds_nothing_when_no_good_qualifies_as_a_store(self):
        self.assertEqual(state_store.orders(setup_with(fixture.specs()), record_with(1.0e6), View()), ([], [], {}))

    def test_the_store_the_state_holds_is_reported_as_kept_for_its_other_lines_to_leave_alone(self):
        _bids, _offers, kept = state_store.orders(setup_with(SPECS), record_with(0.0), View(stocks=metal_stock(5.0)))
        self.assertEqual(kept, {fixture.METAL: 5.0})

    def test_a_state_holding_far_more_than_it_wants_offers_the_excess(self):
        held = 1.0e6
        _bids, offers, _kept = state_store.orders(setup_with(SPECS), record_with(0.0), View(stocks=metal_stock(held)))
        self.assertEqual([offer.good for offer in offers], [fixture.METAL])
        self.assertTrue(0.0 < offers[0].quantity < held)


if __name__ == "__main__":
    unittest.main()
