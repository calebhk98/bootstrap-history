"""Complaint 514: a seat is paid what the clearing paid for its concerns' goods, as a firm is, not the engine's estimate.
The rules are called on built inputs; no game is built."""
QUICK_TOPIC = True

import contextlib
import types
import unittest
from unittest import mock

from sim.agents.api import edges
from sim.ledger.api import PayEdge, ReceiveFromEdge
from sim.markets import port_seats
from sim.production import concern_sales
from sim.refusal import Refusal

PRICE = 3.0
COIN = 2.0


class StandInSim:
    """Records what the acting seat's ledger is credited and charged, by seat, edge and purpose."""
    def __init__(self, seats):
        self.state = types.SimpleNamespace(seats=seats)
        self.acting, self.postings = None, []
        self.scenario = types.SimpleNamespace(act_as=self.act_as)

    @contextlib.contextmanager
    def act_as(self, seat_id):
        self.acting = seat_id
        yield

    def send(self, command):
        sign = {ReceiveFromEdge: 1.0, PayEdge: -1.0}[type(command)]
        self.postings.append((self.acting, command.edge, sign * command.amount, command.purpose))


class RefusesInputs(StandInSim):
    """A stand-in whose seat cannot pay the suppliers' edge."""
    def send(self, command):
        if isinstance(command, PayEdge) and command.edge == edges.EDGE_SUPPLIERS:
            return Refusal("cannot_pay", "no funds")
        if not isinstance(command, (PayEdge, ReceiveFromEdge)):
            return None   # the log line of the refusal
        return super().send(command)


def settle(units_offered, units_taken, inputs_cost, sim=None, dividends=None):
    """The settlement after a clearing in which buyers took `units_taken` of `units_offered` at PRICE."""
    book = types.SimpleNamespace(balance=lambda seat, currency: units_taken * PRICE if seat == "seat" else 0.0)
    economy = types.SimpleNamespace(
        setup=types.SimpleNamespace(coin_per_unit=COIN, currency_id="money"),
        area_map=types.SimpleNamespace(area_of=lambda good, tile: "area"),
        view=lambda: types.SimpleNamespace(price=lambda good, area: PRICE))
    holdings = {"goods": {"acid": {"tile": units_offered - units_taken}}}
    sim = sim or StandInSim({"seat", "idle"})
    api = port_seats.economy_api
    with mock.patch.object(api, "economy_book", lambda eco: book), \
            mock.patch.object(api, "account_holdings", lambda eco, seat: holdings), \
            mock.patch.object(api, "bank_dividends_to", lambda eco, seat: (dividends or {}).get(seat, 0.0)), \
            mock.patch.object(api, "settle_agent_takings", lambda eco, seat, edge: book.balance(seat, "money")):
        sold = port_seats.settle_seats(
            sim, economy, {"seat": ("tile", {"acid": units_offered})}, {"seat": inputs_cost}, "legacy")
    return sim.postings, sold


class SeatIsPaidWhatTheClearingPaid(unittest.TestCase):
    def test_a_seat_offered_a_thousand_units_and_bought_from_for_ten_is_paid_for_ten(self):
        postings, sold = settle(1000.0, 10.0, 0.0)
        credit = [amount for seat, edge, amount, purpose in postings if edge == edges.EDGE_CUSTOMERS]
        self.assertEqual(credit, [10.0 * PRICE * COIN])          # ten units at the cleared price, in coin
        self.assertEqual(sold["seat"]["acid"][:2], [1000.0, 10.0])

    def test_nothing_taken_pays_nothing(self):
        postings, _ = settle(1000.0, 0.0, 0.0)
        self.assertEqual([amount for _, edge, amount, _ in postings if edge == edges.EDGE_CUSTOMERS], [0.0])

    def test_the_inputs_are_charged_so_the_net_is_the_proceeds_less_them(self):
        postings, _ = settle(1000.0, 10.0, 25.0)
        self.assertAlmostEqual(sum(amount for _, _, amount, _ in postings), 10.0 * PRICE * COIN - 25.0)

    def test_a_sale_reversed_because_the_inputs_were_refused_is_returned_as_not_booked(self):
        postings, sold = settle(1000.0, 10.0, 25.0, RefusesInputs({"seat", "idle"}))
        self.assertEqual(sum(amount for _, _, amount, _ in postings), 0.0)
        self.assertEqual(sold["seat"]["acid"], [1000.0, 0.0, 0.0])

    def test_a_seat_that_offered_nothing_is_not_touched(self):
        postings, _ = settle(1000.0, 10.0, 0.0)
        self.assertEqual({seat for seat, _, _, _ in postings}, {"seat"})


class BankDividendsAreNotSales(unittest.TestCase):
    def test_a_dividend_is_its_own_posting_and_the_sale_is_the_takings_less_it(self):
        postings, sold = settle(1000.0, 10.0, 0.0, dividends={"seat": 4.0})
        self.assertIn(("seat", edges.EDGE_INTEREST, 4.0 * COIN, "bank dividend"), postings)
        self.assertIn(("seat", edges.EDGE_CUSTOMERS, 10.0 * PRICE * COIN - 4.0 * COIN, "concern sales"), postings)
        self.assertAlmostEqual(sold["seat"]["acid"][2], (10.0 * PRICE - 4.0) * COIN)   # the proceeds exclude the dividend

    def test_a_dividend_stays_booked_when_the_inputs_are_refused_and_the_sale_is_reversed(self):
        postings, sold = settle(1000.0, 10.0, 25.0, RefusesInputs({"seat", "idle"}), dividends={"seat": 4.0})
        self.assertEqual(sum(amount for _, _, amount, _ in postings), 4.0 * COIN)
        self.assertEqual(sold["seat"]["acid"], [1000.0, 0.0, 0.0])

    def test_a_seat_that_offered_nothing_still_receives_its_dividend(self):
        sim = StandInSim({"seat", "idle"})
        book = types.SimpleNamespace(balance=lambda seat, currency: 5.0 if seat == "idle" else 0.0)
        economy = types.SimpleNamespace(setup=types.SimpleNamespace(coin_per_unit=COIN, currency_id="money"), view=lambda: None)
        api = port_seats.economy_api
        with mock.patch.object(api, "economy_book", lambda eco: book), \
                mock.patch.object(api, "bank_dividends_to", lambda eco, seat: 5.0 if seat == "idle" else 0.0), \
                mock.patch.object(api, "settle_agent_takings", lambda eco, seat, edge: book.balance(seat, "money")):
            port_seats.settle_seats(sim, economy, {}, {}, "legacy")
        self.assertEqual(sim.postings, [("idle", edges.EDGE_INTEREST, 5.0 * COIN, "bank dividend")])

    def test_the_dividend_is_never_more_than_the_takings(self):
        self.assertEqual(port_seats.dividend_of_takings(9.0, 2.0, 10.0), 10.0)
        self.assertEqual(port_seats.dividend_of_takings(3.0, 2.0, 10.0), 6.0)
        self.assertEqual(port_seats.dividend_of_takings(3.0, 2.0, 0.0), 0.0)
        self.assertEqual(port_seats.dividend_of_takings(0.0, 2.0, 10.0), 0.0)


class WhatAConcernPutsInAndTakesOut(unittest.TestCase):
    def test_only_the_goods_the_market_trades_are_offered_at_the_concerns_scale(self):
        offered = concern_sales.offered_units({"acid": 100.0, "dust": 50.0, "salt": 0.0}, 0.5, lambda material: material != "dust")
        self.assertEqual(offered, {"acid": 50.0})

    def test_a_concern_that_runs_nothing_offers_nothing(self):
        self.assertEqual(concern_sales.offered_units({"acid": 100.0}, 0.0, lambda material: True), {})

    def test_inputs_cost_their_price_at_the_concerns_scale_and_an_unpriced_input_is_left_out(self):
        cost = concern_sales.inputs_cost({"ore": 10.0, "fuel": 4.0, "air": 9.0}, 0.5, {"ore": 2.0, "fuel": 5.0}.get)
        self.assertEqual(cost, 10.0 * 0.5 * 2.0 + 4.0 * 0.5 * 5.0)


if __name__ == "__main__":
    unittest.main()
