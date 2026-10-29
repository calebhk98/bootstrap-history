"""The ledger module's money commands, each on plain views: the postings they make between the parties they name, and the
refusals. (Complaint 185, 640: the loss of a payer is the payee's gain, booked by purpose.)"""
QUICK_TOPIC = True

import json
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.agents.api import EDGE_OUTSIDE, ActorRegistry, ActorsState, DUES_CAUSE
from sim.engine.state import ActorRecord, deserialize_state, serialize_state
from sim.ledger.api import (CloseCashPeriod, CreditSeat, DebitSeat, NoteHolderBooking, NoteSeatCash, NoteSpend, OpenCashBook, OpenPurse,
                            BankStock, ChangeStock, DrawDownStock, LedgerSeat, LedgerWorld, PayActor, PayActorFromHousehold, PayEdge, PayExchange,
                            ReceiveFromEdge, ReceiveFromExchange, RescaleHouseholdMoney, RestorePurse, SettleWithEdge, TakeFromHouseholdPurse,
                            WithdrawHouseholdMoney)
from sim.ledger.ledger import Ledger
from sim.refusal import Refusal
from sim.tests import module_harness

SEAT = "founder"


def society(household_money):
    registry = ActorRegistry(ActorsState(home_country="rome_100ad"))
    treasury = registry.ensure_government("rome_100ad")
    household = registry.add("household", ActorRecord(kind="firm", money=household_money))
    return registry, treasury, household


def ledger_over(**views):
    return module_harness.build(Ledger, views=views, module_id="ledger")


def seat_ledger(money=0.0, seats=(SEAT,), **views):
    """A ledger over a real book with the seats `seats` (each in the book, the first holding `money`) and a cast:
    returns (module, registry, treasury). The module acts for the first seat."""
    registry, treasury, _firm = society(0.0)
    slots = {seat_id: LedgerSeat() for seat_id in seats}
    module = ledger_over(cast=registry, cast_state=registry.state, year=100, seat_list={"joined": list(seats)},
                         **views)
    module.seat_slot_of = lambda seat_id: slots[seat_id]
    module.seat = slots[seats[0]]
    module.clock.act_as(seats[0])
    registry.state.purses.set_net(seats[0], money, "set")
    return module, registry, treasury


class PayActorFromHouseholdCommand(unittest.TestCase):
    def test_the_households_loss_is_the_treasurys_gain_booked_by_purpose(self):
        module, _registry, treasury = seat_ledger(1000.0)
        module.pay_actor_from_household(PayActorFromHousehold(treasury.actor_id, 300.0, {"requisition": 200.0, "office": 100.0}))
        self.assertEqual(module.acting_balance(), 700.0)
        self.assertEqual(treasury.money, 300.0)
        self.assertEqual(treasury.record.income, {"requisition": 200.0, "office": 100.0})

    def test_the_payment_is_entered_in_the_seats_cash_book_under_its_causes(self):
        module, _registry, treasury = seat_ledger(1000.0)
        module.pay_actor_from_household(PayActorFromHousehold(treasury.actor_id, 300.0, {"requisition": 200.0, "office": 100.0}))
        self.assertEqual(module.seat.cash_flow, {"requisition": -200.0, "office": -100.0})

    def test_a_household_that_cannot_cover_it_is_paid_into_debt(self):
        module, _registry, treasury = seat_ledger(100.0)
        module.pay_actor_from_household(PayActorFromHousehold(treasury.actor_id, 300.0, "confiscation"))
        self.assertEqual(module.acting_balance(), -200.0)
        self.assertEqual(treasury.money, 300.0)

    def test_an_actor_the_cast_does_not_hold_is_refused_and_nothing_moves(self):
        module, _registry, _treasury = seat_ledger(100.0)
        answer = module.pay_actor_from_household(PayActorFromHousehold("nobody", 30.0, "x"))
        self.assertIsInstance(answer, Refusal)
        self.assertEqual((answer.cause, module.acting_balance()), ("no_such_actor", 100.0))


class TakeFromHouseholdPurseCommand(unittest.TestCase):
    def test_the_purse_is_debited_and_the_taker_credited(self):
        module, _registry, treasury = seat_ledger(500.0)
        module.take_from_household_purse(TakeFromHouseholdPurse(treasury.actor_id, 120.0, "wealth found hidden"))
        self.assertEqual((module.acting_balance(), treasury.money), (380.0, 120.0))
        self.assertEqual(module.seat.cash_flow, {"wealth found hidden": -120.0})

    def test_an_actor_the_cast_does_not_hold_is_refused(self):
        module, _registry, _treasury = seat_ledger(500.0)
        answer = module.take_from_household_purse(TakeFromHouseholdPurse("nobody", 1.0, "x"))
        self.assertEqual((answer.cause, module.acting_balance()), ("no_such_actor", 500.0))


class PayActorCommand(unittest.TestCase):
    """An actor of the cast pays an actor, a seat (as its party) or a government the cast does not hold yet (opened)."""

    def module(self, governments=()):
        opened = []
        registry = SimpleNamespace(
            get=lambda actor_id: SimpleNamespace(actor_id=actor_id) if actor_id.split(":")[-1] in governments or actor_id == "trader" else None,
            ensure_government=lambda country: opened.append(country) or SimpleNamespace(actor_id="government:" + country))
        module = ledger_over(cast=registry, seat_list={"joined": ["seat1"]}, cast_state=SimpleNamespace(purses=object()))
        module.seat_slot_of = lambda seat_id: LedgerSeat()
        return module, opened

    def pay(self, module, payee):
        paid = []
        with mock.patch("sim.ledger.ledger.ledger.transfer", lambda payer, to, amount, cause: paid.append((payer.actor_id, to.actor_id, amount, cause))):
            module.pay_actor(PayActor("trader", payee, 4.0, DUES_CAUSE))
        return paid

    def test_a_seat_is_paid_as_a_party_in_the_book_under_its_own_id(self):
        module, _opened = self.module()
        self.assertEqual(self.pay(module, "seat1"), [("trader", "seat1", 4.0, DUES_CAUSE)])

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
        module, registry, _treasury = seat_ledger(-300.0)
        edge = registry.state.edge("edge:creditors")
        module.settle_with_edge(SettleWithEdge("edge:creditors", -50.0, "debts written off in settlement"))
        self.assertEqual((module.acting_balance(), edge.balance()), (-50.0, -250.0))


class RescaleHouseholdMoneyCommand(unittest.TestCase):
    def test_the_purse_and_the_cash_mark_move_by_the_ratio(self):
        module, _registry, _treasury = seat_ledger(100.0)
        module.seat.cash_mark = 40.0
        module.rescale_household_money(RescaleHouseholdMoney(1.5))
        self.assertEqual((module.acting_balance(), module.seat.cash_mark), (150.0, 60.0))

    def test_a_household_with_no_cash_mark_keeps_none(self):
        module, _registry, _treasury = seat_ledger(10.0)
        module.rescale_household_money(RescaleHouseholdMoney(1.5))
        self.assertEqual((module.acting_balance(), module.seat.cash_mark), (15.0, None))


class WithdrawHouseholdMoneyCommand(unittest.TestCase):
    def test_the_money_falls_by_the_amount(self):
        module, _registry, _treasury = seat_ledger(5000.0)
        module.withdraw_household_money(WithdrawHouseholdMoney(1000.0))
        self.assertEqual(module.acting_balance(), 4000.0)


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


class NoteHolderBookingCommand(unittest.TestCase):
    def booked(self, holder, signed):
        entries = []
        lender = SimpleNamespace(note_income=lambda label, amount: entries.append(("actor in", label, amount)),
                                 note_outlay=lambda label, amount: entries.append(("actor out", label, amount)))
        module, _registry, _treasury = seat_ledger(seats=("seat:a",))
        module.needs.cast = lambda: SimpleNamespace(actors={"abbey": lender})
        module.note_holder_booking(NoteHolderBooking(holder, signed, "loan"))
        return entries, module.seat.cash_flow

    def test_a_seats_posting_is_entered_in_the_seats_own_cash_book_by_its_sign(self):
        self.assertEqual(self.booked("seat:a", 5.0), ([], {"loan": 5.0}))
        self.assertEqual(self.booked("seat:a", -2.0), ([], {"loan": -2.0}))

    def test_an_actors_posting_is_entered_in_its_books(self):
        self.assertEqual(self.booked("abbey", -2.0), ([("actor out", "loan", 2.0)], {}))

    def test_an_edge_or_an_unknown_holder_keeps_no_books(self):
        self.assertEqual(self.booked("edge:savers", 5.0), ([], {}))


class SeatMoneyCommands(unittest.TestCase):
    """The commands the seat's party and the openings send: each moves the named seat's account or its cash book."""

    def test_a_credit_raises_the_purse_and_enters_the_cause(self):
        module, _registry, _treasury = seat_ledger(100.0)
        module.credit_seat(CreditSeat(SEAT, 25.0, "sales"))
        self.assertEqual((module.acting_balance(), module.seat.cash_flow), (125.0, {"sales": 25.0}))

    def test_a_debit_lowers_the_purse_and_enters_the_cause_with_its_sign(self):
        module, _registry, _treasury = seat_ledger(100.0)
        module.debit_seat(DebitSeat(SEAT, 30.0, "living costs"))
        self.assertEqual((module.acting_balance(), module.seat.cash_flow), (70.0, {"living costs": -30.0}))

    def test_a_payment_that_carries_several_causes_enters_each_with_its_own_signed_part(self):
        module, _registry, _treasury = seat_ledger(100.0)
        module.debit_seat(DebitSeat(SEAT, 10.0, {"running costs": 12.0, "sales": -2.0}))
        self.assertEqual(module.seat.cash_flow, {"running costs": -12.0, "sales": 2.0})

    def test_a_named_seat_other_than_the_acting_one_is_the_one_moved(self):
        module, _registry, _treasury = seat_ledger(100.0, seats=(SEAT, "second"))
        module.credit_seat(CreditSeat("second", 5.0, "gift"))
        self.assertEqual((module.acting_balance(), module.seat_balance("second"), module.seat_of("second").cash_flow, module.seat.cash_flow),
                         (100.0, 5.0, {"gift": 5.0}, {}))

    def test_a_posting_the_book_made_is_entered_in_the_cash_book_only(self):
        module, _registry, _treasury = seat_ledger(100.0)
        module.note_seat_cash(NoteSeatCash(SEAT, 1.0, 7.0, "sales"))
        module.note_seat_cash(NoteSeatCash(SEAT, -1.0, 3.0, "sales"))
        self.assertEqual((module.acting_balance(), module.seat.cash_flow), (100.0, {"sales": 4.0}))

    def test_a_mapping_purpose_keeps_its_own_signs_whatever_the_amount(self):
        module, _registry, _treasury = seat_ledger(0.0)
        module.note_seat_cash(NoteSeatCash(SEAT, 1.0, -5.0, {"a": 2.0, "b": -1.0}))
        self.assertEqual(module.seat.cash_flow, {"a": 2.0, "b": -1.0})

    def test_the_purse_is_restored_to_a_figure(self):
        module, _registry, _treasury = seat_ledger(100.0)
        module.restore_purse(RestorePurse(40.0))
        self.assertEqual(module.acting_balance(), 40.0)

    def test_an_edge_pays_in_and_the_seat_pays_out_as_the_seats_own_state_does_it(self):
        module, _registry, _treasury = seat_ledger(100.0)
        module.receive_from_edge(ReceiveFromEdge("edge:customers", 10.0, "venture revenue"))
        module.pay_edge(PayEdge("edge:customers", 4.0, "running costs"))
        self.assertEqual((module.acting_balance(), module.seat.cash_flow), (106.0, {"venture revenue": 10.0, "running costs": -4.0}))

    def test_a_joining_seat_opens_its_account_once_with_what_it_holds(self):
        module, registry, _treasury = seat_ledger(0.0, seats=(SEAT, "second"))
        module.open_purse(OpenPurse("second", 40.0))
        module.open_purse(OpenPurse("second", 99.0))
        self.assertEqual(module.seat_balance("second"), 40.0)

    def test_a_seat_that_holds_nothing_opens_no_account(self):
        module, registry, _treasury = seat_ledger(0.0, seats=(SEAT, "second"))
        module.open_purse(OpenPurse("second", 0.0))
        self.assertFalse(registry.state.purses.has_account("second"))

    def test_the_cash_book_measures_from_the_opening_cash(self):
        module, _registry, _treasury = seat_ledger(100.0)
        module.open_cash_book(OpenCashBook(100.0))
        module.credit_seat(CreditSeat(SEAT, 5.0, "sales"))
        book = module.cash_book()
        self.assertEqual((book["opening"], book["closing"], book["causes"]), (100.0, 105.0, {"sales": 5.0}))
        self.assertEqual(module.cash_unaccounted(), 0.0)

    def test_a_write_around_the_ledger_shows_as_unaccounted_cash(self):
        module, registry, _treasury = seat_ledger(100.0)
        module.open_cash_book(OpenCashBook(100.0))
        registry.state.purses.set_net(SEAT, 109.0, "stray")
        self.assertAlmostEqual(module.cash_unaccounted(), 9.0)

    def test_closing_the_period_starts_the_next_from_todays_cash(self):
        module, _registry, _treasury = seat_ledger(100.0)
        module.open_cash_book(OpenCashBook(100.0))
        module.credit_seat(CreditSeat(SEAT, 5.0, "sales"))
        module.close_cash_period(CloseCashPeriod())
        self.assertEqual((module.seat.cash_flow, module.seat.cash_mark), ({}, 105.0))
        self.assertEqual(module.seat.cash_periods, [{"year": 100, "opening": 100.0, "closing": 105.0, "causes": {"sales": 5.0}}])

    def test_causes_since_a_year_add_the_closed_periods_after_it_to_the_open_one(self):
        module, _registry, _treasury = seat_ledger(100.0)
        module.seat.cash_periods = [{"year": 100, "opening": 0.0, "closing": 0.0, "causes": {"a": 10.0}}]
        module.seat.cash_flow = {"a": 5.0, "b": -2.0}
        self.assertEqual(module.cash_causes_since(99), {"a": 15.0, "b": -2.0})
        self.assertEqual(module.cash_causes_since(100), {"a": 5.0, "b": -2.0})

    def test_the_years_spending_is_counted(self):
        module, _registry, _treasury = seat_ledger(0.0)
        module.note_spend(NoteSpend(40.0))
        module.note_spend(NoteSpend(2.5))
        self.assertEqual(module.seat.total_spend, 42.5)


class SavedWithTheSeat(unittest.TestCase):
    def test_the_cash_book_and_the_years_spending_round_trip_a_save(self):
        seat = LedgerSeat(cash_flow={"sales": 5.0}, cash_mark=40.0, total_spend=3.5,
                          cash_periods=[{"year": 99, "opening": 1.0, "closing": 2.0, "causes": {"a": 1.0}}])
        loaded = deserialize_state(json.loads(json.dumps(serialize_state(seat))), LedgerSeat)
        self.assertEqual(loaded, seat)

    def test_a_seat_with_no_cash_mark_keeps_none_across_a_save(self):
        loaded = deserialize_state(json.loads(json.dumps(serialize_state(LedgerSeat()))), LedgerSeat)
        self.assertIsNone(loaded.cash_mark)


class SeatPostingsNetToZero(unittest.TestCase):
    """Conservation: what a command takes from one account it gives to another, so the book's accounts sum to what they did."""

    def total(self, registry):
        book = registry.state.purses.book
        return sum(book.balance(account, "engine_coin") for account in book.agents())

    def test_a_payment_to_an_actor_moves_the_same_sum_between_accounts(self):
        module, registry, treasury = seat_ledger(1000.0)
        before = self.total(registry)
        module.pay_actor_from_household(PayActorFromHousehold(treasury.actor_id, 300.0, "tax"))
        self.assertAlmostEqual(self.total(registry), before)
        self.assertEqual(registry.state.purses.purse(treasury.account_id), 300.0)

    def test_a_payment_to_an_edge_and_back_nets_to_zero(self):
        module, registry, _treasury = seat_ledger(1000.0)
        before = self.total(registry)
        module.pay_edge(PayEdge("edge:suppliers", 120.0, "running costs"))
        module.receive_from_edge(ReceiveFromEdge("edge:suppliers", 20.0, "refund"))
        self.assertAlmostEqual(self.total(registry), before)
        self.assertEqual(module.acting_balance(), 900.0)

    def test_a_credit_and_a_debit_net_to_zero_across_the_account_and_the_outside(self):
        module, registry, _treasury = seat_ledger(1000.0)
        before = self.total(registry)
        outside_before = registry.state.purses.book.balance(EDGE_OUTSIDE, "engine_coin")
        module.credit_seat(CreditSeat(SEAT, 70.0, "sales"))
        module.debit_seat(DebitSeat(SEAT, 30.0, "costs"))
        self.assertAlmostEqual(self.total(registry), before)
        self.assertAlmostEqual(registry.state.purses.book.balance(EDGE_OUTSIDE, "engine_coin"), outside_before - 40.0)
        self.assertEqual(module.acting_balance(), 1040.0)


if __name__ == "__main__":
    unittest.main()
