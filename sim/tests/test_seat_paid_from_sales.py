"""Complaint 514: a seat is paid what the clearing paid for its concerns' goods, as a firm is, not the engine's estimate.
The rules are called on built inputs; no game is built."""
QUICK_TOPIC = True

import contextlib
import types
import unittest
from unittest import mock

from sim.agents.api import edges
from sim.engine import concern_sales, economy_port_seats

PRICE = 3.0
COIN = 2.0


class StandInSim:
    """Records what the acting seat's ledger is credited and charged, by seat, edge and purpose."""
    def __init__(self, seats):
        self.state = types.SimpleNamespace(seats=seats)
        self.acting, self.postings = None, []

    @contextlib.contextmanager
    def act_as(self, seat_id):
        self.acting = seat_id
        yield

    def receive_from_edge(self, edge, amount, purpose):
        self.postings.append((self.acting, edge, amount, purpose))

    def pay_edge(self, edge, amount, purpose):
        self.postings.append((self.acting, edge, -amount, purpose))


def settle(units_offered, units_taken, inputs_cost):
    """The settlement after a clearing in which buyers took `units_taken` of `units_offered` at PRICE."""
    book = types.SimpleNamespace(balance=lambda seat, currency: units_taken * PRICE if seat == "seat" else 0.0)
    economy = types.SimpleNamespace(
        setup=types.SimpleNamespace(coin_per_unit=COIN, currency_id="money"),
        area_map=types.SimpleNamespace(area_of=lambda good, tile: "area"),
        view=lambda: types.SimpleNamespace(price=lambda good, area: PRICE))
    holdings = {"goods": {"acid": {"tile": units_offered - units_taken}}}
    sim = StandInSim({"seat", "idle"})
    api = economy_port_seats.economy_api
    with mock.patch.object(api, "economy_book", lambda eco: book), \
            mock.patch.object(api, "account_holdings", lambda eco, seat: holdings), \
            mock.patch.object(api, "settle_agent_takings", lambda eco, seat, edge: book.balance(seat, "money")):
        sold, takings = economy_port_seats.settle_seats(
            sim, economy, {"seat": ("tile", {"acid": units_offered})}, {"seat": inputs_cost}, "legacy")
    return sim.postings, sold, takings


class SeatIsPaidWhatTheClearingPaid(unittest.TestCase):
    def test_a_seat_offered_a_thousand_units_and_bought_from_for_ten_is_paid_for_ten(self):
        postings, sold, takings = settle(1000.0, 10.0, 0.0)
        credit = [amount for seat, edge, amount, purpose in postings if edge == edges.EDGE_CUSTOMERS]
        self.assertEqual(credit, [10.0 * PRICE * COIN])          # ten units at the cleared price, in coin
        self.assertEqual(sold["seat"]["acid"][:2], [1000.0, 10.0])
        self.assertEqual(takings["seat"], 10.0 * PRICE * COIN)

    def test_nothing_taken_pays_nothing(self):
        postings, _, takings = settle(1000.0, 0.0, 0.0)
        self.assertEqual([amount for _, edge, amount, _ in postings if edge == edges.EDGE_CUSTOMERS], [0.0])
        self.assertEqual(takings["seat"], 0.0)

    def test_the_inputs_are_charged_so_the_net_is_the_proceeds_less_them(self):
        postings, _, _ = settle(1000.0, 10.0, 25.0)
        self.assertAlmostEqual(sum(amount for _, _, amount, _ in postings), 10.0 * PRICE * COIN - 25.0)

    def test_a_seat_that_offered_nothing_is_not_touched(self):
        postings, _, _ = settle(1000.0, 10.0, 0.0)
        self.assertEqual({seat for seat, _, _, _ in postings}, {"seat"})


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
