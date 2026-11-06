"""Actors that pay for something do with less when they cannot cover it: `ledger.payable`, `pay_up_to` and `pay_in_full` over
two firms in the one book, and the upkeep a plant's owner pays."""

QUICK_TOPIC = True

import types
import unittest

from sim.agents import ledger
from sim.agents.api import ActorRecord, ActorsState
from sim.agents.edges import EDGE_SUPPLIERS, Edge
from sim.agents.firm import Firm

from .pool_lenders import lend_through


def two_firms(held, offered_units=0.0):
    state = ActorsState()
    payer = Firm("firm:payer", ActorRecord(kind="firm"))
    payee = Firm("firm:payee", ActorRecord(kind="firm"))
    for actor in (payer, payee):
        actor.attach(state.purses)
    payer.money = held
    if offered_units:
        lend_through(state.purses, {"cohort:a": (offered_units, 0.05)}, coin_per_unit=1.0)
    return state, payer, payee


class PayUpTo(unittest.TestCase):
    def test_a_payer_with_less_than_the_amount_pays_what_it_holds_and_the_payee_gets_it(self):
        _state, payer, payee = two_firms(40.0)
        self.assertEqual(ledger.pay_up_to(payer, payee, 100.0, "test"), 40.0)
        self.assertEqual((payer.money, payee.money), (0.0, 40.0))

    def test_what_the_lenders_will_lend_adds_to_what_it_can_pay(self):
        _state, payer, payee = two_firms(40.0, offered_units=25.0)
        self.assertAlmostEqual(ledger.pay_up_to(payer, payee, 100.0, "test"), 65.0)
        self.assertAlmostEqual(payer.money, -25.0)

    def test_a_payer_that_can_pay_it_all_pays_it_all(self):
        _state, payer, payee = two_firms(500.0)
        self.assertEqual(ledger.pay_up_to(payer, payee, 100.0, "test"), 100.0)

    def test_a_payer_outside_the_one_book_is_never_short(self):
        self.assertEqual(ledger.payable(types.SimpleNamespace(), 70.0), 70.0)


class PayInFull(unittest.TestCase):
    def test_a_payer_short_of_the_amount_pays_nothing_and_says_so(self):
        _state, payer, payee = two_firms(40.0)
        self.assertFalse(ledger.pay_in_full(payer, payee, 100.0, "test"))
        self.assertEqual((payer.money, payee.money), (40.0, 0.0))

    def test_a_payer_that_can_cover_it_pays_and_says_so(self):
        _state, payer, payee = two_firms(140.0)
        self.assertTrue(ledger.pay_in_full(payer, payee, 100.0, "test"))
        self.assertEqual((payer.money, payee.money), (40.0, 100.0))


class PayingAnEdge(unittest.TestCase):
    def test_an_owner_short_of_a_charge_to_an_edge_pays_what_it_holds_instead_of_raising(self):
        state, owner, _payee = two_firms(30.0)
        self.assertEqual(ledger.pay_up_to(owner, Edge(EDGE_SUPPLIERS, state.purses), 80.0, "upkeep"), 30.0)
        self.assertEqual(owner.money, 0.0)


if __name__ == "__main__":
    unittest.main()
