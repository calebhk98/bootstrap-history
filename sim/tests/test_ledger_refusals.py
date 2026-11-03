"""A ledger payment the book refuses (the payer cannot cover it) answers a Refusal with the cause `cannot_pay`, moves nothing and
enters nothing in the books: the caller does with less."""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.book import InsufficientFunds
from sim.ledger.api import PayActor, PayActorFromHousehold, PayEdgeFrom, PayExchange, TakeFromHouseholdPurse
from sim.refusal import Refusal
from sim.tests.test_ledger_commands import ledger_over, seat_ledger, society


def refuse(*_arguments):
    raise InsufficientFunds("the payer holds nothing")


class RefusedPayments(unittest.TestCase):
    def test_pay_edge_from_answers_a_refusal(self):
        registry, _treasury, firm = society(10.0)
        module = ledger_over(cast=registry, cast_state=registry.state)
        with mock.patch("sim.ledger.ledger.ledger.transfer", refuse):
            answer = module.pay_edge_from(PayEdgeFrom(firm.actor_id, "edge:thieves", 50.0, "theft"))
        self.assertIsInstance(answer, Refusal)
        self.assertEqual(answer.cause, "cannot_pay")

    def test_pay_actor_answers_a_refusal(self):
        registry, treasury, firm = society(10.0)
        module = ledger_over(cast=registry, seat_list={"joined": []})
        with mock.patch("sim.ledger.ledger.ledger.transfer", refuse):
            answer = module.pay_actor(PayActor(firm.actor_id, treasury.actor_id, 50.0, "licence"))
        self.assertEqual(answer.cause, "cannot_pay")

    def test_pay_actor_from_household_answers_a_refusal(self):
        module, _registry, treasury = seat_ledger(100.0)
        with mock.patch("sim.ledger.ledger.ledger.transfer", refuse):
            answer = module.pay_actor_from_household(PayActorFromHousehold(treasury.actor_id, 300.0, "tax"))
        self.assertEqual((answer.cause, module.acting_balance(), treasury.money), ("cannot_pay", 100.0, 0.0))

    def test_take_from_household_purse_answers_a_refusal(self):
        module, _registry, treasury = seat_ledger(100.0)
        with mock.patch("sim.ledger.ledger.ledger.transfer", refuse):
            answer = module.take_from_household_purse(TakeFromHouseholdPurse(treasury.actor_id, 300.0, "seized"))
        self.assertEqual((answer.cause, module.acting_balance()), ("cannot_pay", 100.0))

    def test_pay_exchange_answers_a_refusal_and_enters_no_outlay(self):
        registry, _treasury, firm = society(10.0)
        with mock.patch.object(type(registry.state.purses), "transfer", refuse):
            answer = ledger_over(cast=registry).pay_exchange(PayExchange(firm.actor_id, 500.0, "market purchases"))
        self.assertIsInstance(answer, Refusal)
        self.assertEqual((answer.cause, firm.money, firm.record.outlays), ("cannot_pay", 10.0, {}))


if __name__ == "__main__":
    unittest.main()
