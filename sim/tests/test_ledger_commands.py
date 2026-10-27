"""The ledger module's money commands, each on plain views: the postings they make between the parties they name, and the
refusals. (Complaint 185, 640: the loss of a payer is the payee's gain, booked by purpose.)"""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.agents.api import ActorRegistry, ActorsState, DUES_CAUSE
from sim.engine.state import ActorRecord
from sim.ledger.api import (PayActor, PayActorFromHousehold, RescaleHouseholdMoney, SettleWithEdge, TakeFromHouseholdPurse,
                            WithdrawHouseholdMoney)
from sim.ledger.ledger import Ledger
from sim.refusal import Refusal
from sim.tests import module_harness


def society(household_money):
    registry = ActorRegistry(ActorsState(home_country="rome_100ad"))
    treasury = registry.ensure_government("rome_100ad")
    household = registry.add("household", ActorRecord(kind="firm", money=household_money))
    return registry, treasury, household


def ledger_over(**views):
    return module_harness.build(Ledger, views=views, module_id="ledger")


class PayActorFromHouseholdCommand(unittest.TestCase):
    def test_the_households_loss_is_the_treasurys_gain_booked_by_purpose(self):
        registry, treasury, household = society(1000.0)
        module = ledger_over(cast=registry, legacy_household_actor=household)
        module.pay_actor_from_household(PayActorFromHousehold(treasury.actor_id, 300.0, {"requisition": 200.0, "office": 100.0}))
        self.assertEqual(household.money, 700.0)
        self.assertEqual(treasury.money, 300.0)
        self.assertEqual(treasury.record.income, {"requisition": 200.0, "office": 100.0})

    def test_a_household_that_cannot_cover_it_is_paid_into_debt(self):
        registry, treasury, household = society(100.0)
        ledger_over(cast=registry, legacy_household_actor=household).pay_actor_from_household(
            PayActorFromHousehold(treasury.actor_id, 300.0, "confiscation"))
        self.assertEqual(household.money, -200.0)
        self.assertEqual(treasury.money, 300.0)

    def test_an_actor_the_cast_does_not_hold_is_refused_and_nothing_moves(self):
        registry, _treasury, household = society(100.0)
        answer = ledger_over(cast=registry, legacy_household_actor=household).pay_actor_from_household(
            PayActorFromHousehold("nobody", 30.0, "x"))
        self.assertIsInstance(answer, Refusal)
        self.assertEqual((answer.cause, household.money), ("no_such_actor", 100.0))


class TakeFromHouseholdPurseCommand(unittest.TestCase):
    def test_the_purse_is_debited_and_the_taker_credited(self):
        registry, treasury, _household = society(0.0)
        purse = SimpleNamespace(capital=500.0, debit=lambda amount, purpose: setattr(purse, "capital", purse.capital - amount))
        ledger_over(cast=registry, legacy_acting_household=purse).take_from_household_purse(
            TakeFromHouseholdPurse(treasury.actor_id, 120.0, "wealth found hidden"))
        self.assertEqual((purse.capital, treasury.money), (380.0, 120.0))

    def test_an_actor_the_cast_does_not_hold_is_refused(self):
        registry, _treasury, _household = society(0.0)
        purse = SimpleNamespace(capital=500.0)
        answer = ledger_over(cast=registry, legacy_acting_household=purse).take_from_household_purse(TakeFromHouseholdPurse("nobody", 1.0, "x"))
        self.assertEqual((answer.cause, purse.capital), ("no_such_actor", 500.0))


class PayActorCommand(unittest.TestCase):
    """An actor of the cast pays an actor, a seat (as its party) or a government the cast does not hold yet (opened)."""

    def module(self, governments=()):
        opened = []
        registry = SimpleNamespace(
            get=lambda actor_id: SimpleNamespace(actor_id=actor_id) if actor_id.split(":")[-1] in governments or actor_id == "trader" else None,
            ensure_government=lambda country: opened.append(country) or SimpleNamespace(actor_id="government:" + country))
        module = ledger_over(cast=registry, legacy_seats={"seat1": None}, seat_party=lambda seat_id: SimpleNamespace(actor_id="party of " + seat_id))
        return module, opened

    def pay(self, module, payee):
        paid = []
        with mock.patch("sim.ledger.ledger.ledger.transfer", lambda payer, to, amount, cause: paid.append((payer.actor_id, to.actor_id, amount, cause))):
            module.pay_actor(PayActor("trader", payee, 4.0, DUES_CAUSE))
        return paid

    def test_a_seat_is_paid_as_its_party(self):
        module, _opened = self.module()
        self.assertEqual(self.pay(module, "seat1"), [("trader", "party of seat1", 4.0, DUES_CAUSE)])

    def test_a_government_the_cast_holds_is_paid_without_opening_another(self):
        module, opened = self.module(governments=("rome",))
        self.assertEqual(self.pay(module, "government:rome"), [("trader", "government:rome", 4.0, DUES_CAUSE)])
        self.assertEqual(opened, [])

    def test_a_government_the_cast_lacks_is_opened_for_the_payment(self):
        module, opened = self.module()
        self.assertEqual(self.pay(module, "government:carthage"), [("trader", "government:carthage", 4.0, DUES_CAUSE)])
        self.assertEqual(opened, ["carthage"])


class SettleWithEdgeCommand(unittest.TestCase):
    def test_the_household_is_brought_to_the_balance_by_moving_the_difference_over_the_edge(self):
        registry, _treasury, household = society(-300.0)
        edge = registry.add("edge", ActorRecord(kind="firm", money=0.0))
        module = ledger_over(legacy_household_actor=household, legacy_edge_account={"edge:creditors": edge})
        module.settle_with_edge(SettleWithEdge("edge:creditors", -50.0, "debts written off in settlement"))
        self.assertEqual((household.money, edge.money), (-50.0, -250.0))


class RescaleHouseholdMoneyCommand(unittest.TestCase):
    def test_the_purse_and_the_cash_mark_move_by_the_ratio(self):
        household = SimpleNamespace(capital=100.0, cash_mark=40.0)
        ledger_over(legacy_acting_household=household).rescale_household_money(RescaleHouseholdMoney(1.5))
        self.assertEqual((household.capital, household.cash_mark), (150.0, 60.0))

    def test_a_household_with_no_cash_mark_keeps_none(self):
        household = SimpleNamespace(capital=10.0, cash_mark=None)
        ledger_over(legacy_acting_household=household).rescale_household_money(RescaleHouseholdMoney(1.5))
        self.assertEqual((household.capital, household.cash_mark), (15.0, None))


class WithdrawHouseholdMoneyCommand(unittest.TestCase):
    def test_the_money_falls_by_the_amount(self):
        household = SimpleNamespace(money=5000.0)
        ledger_over(legacy_household_actor=household).withdraw_household_money(WithdrawHouseholdMoney(1000.0))
        self.assertEqual(household.money, 4000.0)


if __name__ == "__main__":
    unittest.main()
