"""Complaint 599: a route's dues are paid into the treasury of the holder of each tile, and a trader's cargo to a partner pays them
without passing the freight. `pay_dues`, `route_dues_by_holder` and the two `pay_route_dues` methods, each called once on a
stand-in with its collaborators replaced by recorders (no game). Who is owed what is test_route_dues_owner."""
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.engine.agents_port_trade import TradeView
from sim.engine.haul_route import Leg, Route
from sim.agents import route_dues_pay
from sim.engine import route_dues
from sim.engine.route_dues import RouteDuesMixin

QUICK_TOPIC = True

ROUTE = Route((Leg("a", "b", "river_boat", 10.0, 1.0), Leg("b", "c", "sail", 50.0, 1.0)))
DUES = {"river_boat": 2.0, "sail": 3.0}


class PayDues(unittest.TestCase):
    """`pay_dues` with the ledger's transfer replaced by a recorder."""

    def pay(self, owed, limit=None):
        transfers = []
        with mock.patch.object(route_dues_pay.ledger, "transfer", lambda payer, payee, amount, cause: transfers.append((payee, amount))):
            paid = route_dues_pay.pay_dues("payer", owed, lambda holder: "treasury of " + holder, limit)
        return paid, transfers

    def test_each_holder_is_paid_its_dues_into_its_own_treasury_in_sorted_order(self):
        paid, transfers = self.pay({"rome": 20.0, "carthage": 30.0})
        self.assertEqual(transfers, [("treasury of carthage", 30.0), ("treasury of rome", 20.0)])
        self.assertEqual(paid, 50.0)

    def test_a_limit_scales_every_holders_share_down_together(self):
        paid, transfers = self.pay({"rome": 20.0, "carthage": 30.0}, limit=25.0)
        self.assertEqual(paid, 25.0)
        self.assertEqual(transfers, [("treasury of carthage", 15.0), ("treasury of rome", 10.0)])

    def test_a_limit_above_the_total_changes_nothing(self):
        self.assertEqual(self.pay({"rome": 20.0}, limit=1000.0)[0], 20.0)

    def test_a_holder_owed_nothing_is_not_paid(self):
        self.assertEqual(self.pay({"rome": 0.0})[1], [])


class RouteDuesByHolder(unittest.TestCase):
    """`RouteDuesMixin.route_dues_by_holder` with the geography rule replaced by a recorder."""

    def test_the_legs_modes_dues_owners_and_tonnes_are_handed_to_the_rule(self):
        asked = []
        game = SimpleNamespace(route_dues_per_tonne_by_mode=lambda: DUES, tile_owner="owner function")
        with mock.patch.object(route_dues, "route_dues_by_holder", lambda *args: asked.append(args) or {"rome": 1.0}):
            result = RouteDuesMixin.route_dues_by_holder(game, ROUTE, 10.0)
        legs = [{"from": "a", "mode": "river_boat"}, {"from": "b", "mode": "sail"}]
        self.assertEqual(asked, [(legs, DUES, "owner function", 10.0)])
        self.assertEqual(result, {"rome": 1.0})


class PayRouteDues(unittest.TestCase):
    """`RouteDuesMixin.pay_route_dues` with the dues sum and the payment replaced by recorders."""

    def test_the_payer_pays_what_the_route_owes_into_the_treasury_lookup_with_the_limit(self):
        asked = []
        game = SimpleNamespace(route_dues_by_holder=lambda route, tonnes: {"rome": tonnes}, route_dues_treasury="treasury function")
        with mock.patch.object(route_dues, "pay_dues", lambda *args: asked.append(args) or 7.0):
            paid = RouteDuesMixin.pay_route_dues(game, "payer", ROUTE, 10.0, limit=5.0)
        self.assertEqual(asked, [("payer", {"rome": 10.0}, "treasury function", 5.0)])
        self.assertEqual(paid, 7.0)


class Cargo(TradeView):
    """The real trade view over a sim that holds partners' routes and pays dues for them."""

    def __init__(self, facts, dues_paid):
        self._sim = SimpleNamespace(civ={"id": "home"}, _foreign_economy_facts=facts.get,
                                    pay_route_dues=lambda payer, route, tonnes, limit=None: dues_paid(route, tonnes, limit))


class PartnerCargo(unittest.TestCase):

    def test_the_dues_of_a_partner_route_are_limited_to_that_routes_freight(self):
        asked = []
        facts = {"han": {"route": ROUTE, "freight_per_tonne": 4.0}}
        cargo = Cargo(facts, lambda route, tonnes, limit: asked.append((route, tonnes, limit)) or 7.0)
        paid = cargo.pay_route_dues("payer", "home", "han", "grain", 10.0)
        self.assertEqual(asked, [(ROUTE, 10.0, 40.0)])
        self.assertEqual(paid, 7.0)

    def test_a_partner_with_no_route_pays_nothing(self):
        cargo = Cargo({"han": {"route": None, "freight_per_tonne": 4.0}}, lambda route, tonnes, limit: 99.0)
        self.assertEqual(cargo.pay_route_dues("payer", "home", "han", "grain", 10.0), 0.0)

    def test_a_cargo_that_goes_nowhere_pays_nothing(self):
        self.assertEqual(Cargo({}, lambda route, tonnes, limit: 99.0).pay_route_dues("payer", "home", "home", "grain", 10.0), 0.0)

    def test_both_ends_pay_when_neither_is_home(self):
        asked = []
        facts = {"han": {"route": ROUTE, "freight_per_tonne": 4.0}, "norse": {"route": ROUTE, "freight_per_tonne": 6.0}}
        cargo = Cargo(facts, lambda route, tonnes, limit: asked.append(limit) or 1.0)
        self.assertEqual(cargo.pay_route_dues("payer", "han", "norse", "grain", 10.0), 2.0)
        self.assertEqual(asked, [40.0, 60.0])


if __name__ == "__main__":
    unittest.main()
