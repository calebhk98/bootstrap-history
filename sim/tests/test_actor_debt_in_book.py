"""An actor's money is an account in the purses' book, never below zero; what it owes is a loan claim the household
savers hold against it. `Actor.money` is the net position, so every reader of it sees what it saw before."""

QUICK_TOPIC = True

import unittest

from sim.agents import ledger
from sim.agents.api import ActorRecord, ActorsState
from sim.agents.firm import Firm
from sim.agents.purses import COIN, EDGE_SAVERS
from sim.engine.state import deserialize_state, serialize_state

from .agents_fake_world import FakeWorld


def pair(money=100.0):
    state = ActorsState()
    first = Firm("first", ActorRecord(kind="firm", money=money))
    second = Firm("second", ActorRecord(kind="firm"))
    for actor in (first, second):
        actor.attach(state.purses)
    return state, first, second


class ActorDebtInBook(unittest.TestCase):
    def test_a_record_created_with_money_places_it_in_the_book(self):
        state, first, _second = pair(100.0)
        self.assertEqual(state.purses.purse("first"), 100.0)
        self.assertEqual(first.record.money, 0.0)
        self.assertEqual(first.money, 100.0)

    def test_paying_more_than_the_purse_draws_the_rest_as_a_claim(self):
        state, first, second = pair(100.0)
        ledger.transfer(first, second, 250.0, "buy")
        purses = state.purses
        self.assertEqual(purses.purse("first"), 0.0)
        self.assertEqual(purses.debt("first"), 150.0)
        self.assertEqual(first.money, -150.0)
        self.assertEqual(first.debt(), 150.0)
        self.assertEqual(second.money, 250.0)
        self.assertEqual(purses.claims["first"].lender, EDGE_SAVERS)
        self.assertEqual(purses.book.balance(EDGE_SAVERS, COIN), -150.0)

    def test_money_coming_in_repays_the_claim_first(self):
        state, first, second = pair(100.0)
        ledger.transfer(first, second, 250.0, "buy")
        ledger.transfer(second, first, 200.0, "sell")
        self.assertEqual(state.purses.debt("first"), 0.0)
        self.assertEqual(state.purses.purse("first"), 50.0)
        self.assertEqual(first.money, 50.0)
        self.assertNotIn("first", state.purses.claims)

    def test_no_purse_goes_below_zero_and_the_book_balances(self):
        state, first, second = pair(10.0)
        for amount in (30.0, 5.0, 80.0):
            ledger.transfer(first, second, amount, "buy")
            ledger.transfer(second, first, amount / 2.0, "sell")
        for account in ("first", "second"):
            self.assertGreaterEqual(state.purses.purse(account), 0.0)
        self.assertAlmostEqual(state.purses.book.total(COIN), 0.0, places=9)
        self.assertAlmostEqual(first.money + second.money, 10.0)   # only what the opening placed in the book

    def test_setting_money_below_zero_is_a_claim_not_a_negative_purse(self):
        state, first, _second = pair(0.0)
        first.money = -40.0
        self.assertEqual(state.purses.purse("first"), 0.0)
        self.assertEqual(state.purses.debt("first"), 40.0)
        self.assertEqual(first.money, -40.0)

    def test_a_payment_to_an_edge_and_back_keeps_the_net_position(self):
        state, first, _second = pair(100.0)
        edge = state.edge("edge:test")
        ledger.transfer(first, edge, 130.0, "tax")
        self.assertEqual(first.money, -30.0)
        self.assertEqual(edge.balance(), 130.0)
        self.assertEqual(edge.volume(), 130.0)
        ledger.transfer(edge, first, 30.0, "refund")
        self.assertEqual(first.money, 0.0)

    def test_interest_on_a_debt_is_added_to_the_claim(self):
        state, first, _second = pair(0.0)
        first.money = -100.0
        world = FakeWorld()
        world.edge_book = state
        first.pay_interest(world)
        self.assertGreater(state.purses.debt("first"), 100.0)
        self.assertEqual(state.purses.purse("first"), 0.0)

    def test_the_claims_survive_a_save_and_a_load(self):
        state, first, second = pair(100.0)
        ledger.transfer(first, second, 250.0, "buy")
        again = deserialize_state(serialize_state(state), ActorsState)
        self.assertEqual(again.purses.debt("first"), 150.0)
        self.assertEqual(again.purses.purse("second"), 250.0)
        self.assertEqual(again.purses.book.balance(EDGE_SAVERS, COIN), -150.0)


if __name__ == "__main__":
    unittest.main()
