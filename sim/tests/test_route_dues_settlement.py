"""Complaint 599: a route's dues are paid into the treasury of the holder of each tile, scale with the tonnes, move with a change
of holder, and a trader's cargo to a partner pays them without passing the freight. `pay_route_dues` of the real
mixins on stand-ins that hold an owner map, accounts and a route (no game). Who is owed what is test_route_dues_owner."""
import unittest
from types import SimpleNamespace

from sim.engine.agents_port_trade import TradeView
from sim.engine.haul_route import Leg, Route
from sim.engine.route_dues import RouteDuesMixin

QUICK_TOPIC = True

ROUTE = Route((Leg("a", "b", "river_boat", 10.0, 1.0), Leg("b", "c", "sail", 50.0, 1.0)))
DUES = {"river_boat": 2.0, "sail": 3.0}


class Account:
    """A payer or a treasury: debit and credit keep a running balance."""

    def __init__(self, money=0.0):
        self.money = money

    def debit(self, amount, purpose):
        self.money -= amount

    def credit(self, amount, purpose):
        self.money += amount

    def note_outlay(self, purpose, amount):
        pass

    def note_income(self, purpose, amount):
        pass


class Haul(RouteDuesMixin):
    """The real dues mixin over an owner map, a dues table and one treasury per holder."""

    def __init__(self, owners):
        self.owners = dict(owners)
        self.treasuries = {}

    def route_dues_per_tonne_by_mode(self):
        return DUES

    def tile_owner(self, tile):
        return self.owners.get(tile)

    def route_dues_treasury(self, holder):
        return self.treasuries.setdefault(holder, Account())


class DuesSettled(unittest.TestCase):

    def test_each_holder_is_paid_for_the_tile_it_holds_and_the_payer_pays_the_sum(self):
        haul, payer = Haul({"a": "rome", "b": "carthage"}), Account(1000.0)
        paid = haul.pay_route_dues(payer, ROUTE, 10.0)
        self.assertAlmostEqual(haul.treasuries["rome"].money, 2.0 * 10.0)
        self.assertAlmostEqual(haul.treasuries["carthage"].money, 3.0 * 10.0)
        self.assertAlmostEqual(paid, 50.0)
        self.assertAlmostEqual(payer.money, 1000.0 - 50.0)

    def test_the_dues_scale_with_the_tonnes(self):
        haul = Haul({"a": "rome", "b": "rome"})
        ten = haul.pay_route_dues(Account(), ROUTE, 10.0)
        twenty = haul.pay_route_dues(Account(), ROUTE, 20.0)
        self.assertGreater(ten, 0.0)
        self.assertAlmostEqual(twenty, 2.0 * ten)

    def test_a_change_of_holder_moves_the_revenue_to_the_new_holder(self):
        haul = Haul({"a": "rome", "b": "rome"})
        haul.pay_route_dues(Account(), ROUTE, 10.0)
        before = haul.treasuries["rome"].money
        haul.owners.update({"a": "second", "b": "second"})
        haul.pay_route_dues(Account(), ROUTE, 10.0)
        self.assertAlmostEqual(haul.treasuries["second"].money, before)
        self.assertEqual(haul.treasuries["rome"].money, before)

    def test_a_limit_scales_every_holders_share_down_together(self):
        haul = Haul({"a": "rome", "b": "carthage"})
        paid = haul.pay_route_dues(Account(), ROUTE, 10.0, limit=25.0)
        self.assertAlmostEqual(paid, 25.0)
        self.assertAlmostEqual(haul.treasuries["rome"].money / haul.treasuries["carthage"].money, 2.0 / 3.0)

    def test_untaxed_tiles_pay_nothing(self):
        haul = Haul({})
        self.assertEqual(haul.pay_route_dues(Account(), ROUTE, 10.0), 0.0)


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
        paid = cargo.pay_route_dues(Account(), "home", "han", "grain", 10.0)
        self.assertEqual(asked, [(ROUTE, 10.0, 40.0)])
        self.assertEqual(paid, 7.0)

    def test_a_partner_with_no_route_pays_nothing(self):
        cargo = Cargo({"han": {"route": None, "freight_per_tonne": 4.0}}, lambda route, tonnes, limit: 99.0)
        self.assertEqual(cargo.pay_route_dues(Account(), "home", "han", "grain", 10.0), 0.0)

    def test_a_cargo_that_goes_nowhere_pays_nothing(self):
        self.assertEqual(Cargo({}, lambda route, tonnes, limit: 99.0).pay_route_dues(Account(), "home", "home", "grain", 10.0), 0.0)

    def test_both_ends_pay_when_neither_is_home(self):
        asked = []
        facts = {"han": {"route": ROUTE, "freight_per_tonne": 4.0}, "norse": {"route": ROUTE, "freight_per_tonne": 6.0}}
        cargo = Cargo(facts, lambda route, tonnes, limit: asked.append(limit) or 1.0)
        self.assertEqual(cargo.pay_route_dues(Account(), "han", "norse", "grain", 10.0), 2.0)
        self.assertEqual(asked, [40.0, 60.0])


if __name__ == "__main__":
    unittest.main()
