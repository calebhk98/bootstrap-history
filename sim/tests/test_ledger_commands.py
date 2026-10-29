"""The ledger module's money commands, each on plain views: the postings they make between the parties they name, and the
refusals. (Complaint 185, 640: the loss of a payer is the payee's gain, booked by purpose.)"""
QUICK_TOPIC = True

import contextlib
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.agents.api import ActorRegistry, ActorsState, DUES_CAUSE
from sim.engine.state import ActorRecord
from sim.ledger.api import (NoteHolderBooking, SettleHouseholdInterest, BankStock, ChangeStock, DrawDownStock, LedgerSeat, LedgerWorld, PayActor, PayActorFromHousehold, PayExchange, ReceiveFromExchange, RescaleHouseholdMoney, SettleWithEdge, TakeFromHouseholdPurse,
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
        module = ledger_over(cast=registry, seat_list={"joined": ["seat1"]}, seat_party=lambda seat_id: SimpleNamespace(actor_id="party of " + seat_id))
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


class ExchangeCommands(unittest.TestCase):
    def test_coin_put_into_the_exchange_leaves_the_actors_purse_and_is_an_outlay(self):
        registry, _treasury, firm = society(500.0)
        ledger_over(cast=registry).pay_exchange(PayExchange(firm.actor_id, 120.0, "market purchases"))
        self.assertEqual(firm.money, 380.0)
        self.assertEqual(firm.record.outlays, {"market purchases": 120.0})

    def test_coin_the_exchange_returns_enters_the_purse_and_is_income_under_its_label(self):
        registry, _treasury, firm = society(500.0)
        ledger_over(cast=registry).receive_from_exchange(ReceiveFromExchange(firm.actor_id, 75.0, "market sales"))
        self.assertEqual(firm.money, 575.0)
        self.assertEqual(firm.record.income, {"market sales": 75.0})


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


class TonnesLedgerState(unittest.TestCase):
    """The seat's tonnes ledger and the capacity pool are the ledger's own state."""

    def module(self, stock=None):
        return module_harness.build(Ledger, views={"year": 100}, seat=LedgerSeat(_material_stock_ledger=stock), world=LedgerWorld(), module_id="ledger")

    def test_a_change_is_counted_in_the_stock_and_in_the_years_opening_snapshot(self):
        module = self.module({"iron": 2.0})
        module.change_stock(ChangeStock("iron", 3.0))
        self.assertEqual(module.seat._material_stock_ledger["iron"], 5.0)
        self.assertEqual(module.seat._material_stock_opening, {"year": 100, "tonnes": {"iron": 5.0}})

    def test_the_first_change_of_the_year_snapshots_the_stock_before_it(self):
        module = self.module({"iron": 2.0})
        module.bank_stock(BankStock((("iron", 4.0),)))
        self.assertEqual(module.seat._material_stock_opening["tonnes"], {"iron": 2.0})
        self.assertEqual(module.seat._material_stock_ledger["iron"], 4.0)

    def test_drawing_down_never_takes_the_stock_below_zero(self):
        module = self.module({"grain": 1.0})
        module.draw_down_stock(DrawDownStock("grain", 5.0))
        self.assertEqual(module.seat._material_stock_ledger["grain"], 0.0)

    def test_capacity_keys_are_swept_out_of_the_ledger_into_the_worlds_pool(self):
        module = self.module({"iron": 1.0, "scholar_hours": 40.0})
        self.assertEqual(dict(module.held_goods()), {"iron": 1.0})
        self.assertEqual(module.world.capacity_pool, {"scholar_hours": 40.0})


class SettleHouseholdInterestCommand(unittest.TestCase):
    def test_the_household_actor_settles_the_year_against_the_actors_world_and_the_answer_is_handed_back(self):
        world = object()
        actor = SimpleNamespace(settle_interest=lambda seen: (30.0, 20.0) if seen is world else None)
        module = ledger_over(legacy_household_actor=actor, actor_world=world)
        self.assertEqual(module.settle_household_interest(SettleHouseholdInterest()), (30.0, 20.0))


class NoteHolderBookingCommand(unittest.TestCase):
    def booked(self, holder, signed):
        entries = []
        household = SimpleNamespace(note_income=lambda label, amount: entries.append(("in", label, amount)),
                                    note_outlay=lambda label, amount: entries.append(("out", label, amount)))
        lender = SimpleNamespace(note_income=lambda label, amount: entries.append(("actor in", label, amount)),
                                 note_outlay=lambda label, amount: entries.append(("actor out", label, amount)))
        self.acting = []

        @contextlib.contextmanager
        def acting_as(seat_id):
            self.acting.append(seat_id)
            yield

        module = ledger_over(seat_list={"joined": ["seat:a"]}, acting_as=acting_as, legacy_acting_household=household,
                             cast=SimpleNamespace(actors={"abbey": lender}))
        module.note_holder_booking(NoteHolderBooking(holder, signed, "loan"))
        return entries

    def test_a_seats_posting_is_entered_in_the_seats_own_books_by_its_sign(self):
        self.assertEqual(self.booked("seat:a", 5.0), [("in", "loan", 5.0)])
        self.assertEqual(self.acting, ["seat:a"])
        self.assertEqual(self.booked("seat:a", -2.0), [("out", "loan", 2.0)])

    def test_an_actors_posting_is_entered_in_its_books(self):
        self.assertEqual(self.booked("abbey", -2.0), [("actor out", "loan", 2.0)])

    def test_an_edge_or_an_unknown_holder_keeps_no_books(self):
        self.assertEqual(self.booked("edge:savers", 5.0), [])


if __name__ == "__main__":
    unittest.main()
