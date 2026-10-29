"""Complaint 599: a route's dues are paid into the treasury of the holder of each tile, and a trader's cargo to a partner pays them
without passing the freight. `dues_payments` is a plain rule; the freight module's `PayRouteDues` is read on plain views (the
holders of the tiles, the wage, the treasuries) and the `PayActor` commands it sends; the trade view hands the partner route
and its freight to the sim's `pay_route_dues`. Who is owed what is test_route_dues_owner."""
import unittest
from types import SimpleNamespace

from sim.agents.api import DUES_CAUSE

from sim.actors.world_trade import TradeView
from sim.tests.world_stand_in import fake_needs
from sim.freight import rules
from sim.freight.commands import PayRouteDues
from sim.freight.module import Freight
from sim.freight.route import Leg, Route
from sim.geography.api import dues_hours_per_tonne
from sim.ledger.api import PayActor
from sim.tests import land_views, module_harness

QUICK_TOPIC = True

ROUTE = Route((Leg("a", "b", "river_boat", 10.0, 1.0), Leg("b", "c", "sail", 50.0, 1.0)))
WAGE = 5.0
PAYER = SimpleNamespace(actor_id="payer")


class DuesPayments(unittest.TestCase):

    def test_each_holder_is_paid_its_dues_in_sorted_order(self):
        self.assertEqual(rules.dues_payments({"rome": 20.0, "carthage": 30.0}, None), [("carthage", 30.0), ("rome", 20.0)])

    def test_a_limit_scales_every_holders_share_down_together(self):
        self.assertEqual(rules.dues_payments({"rome": 20.0, "carthage": 30.0}, 25.0), [("carthage", 15.0), ("rome", 10.0)])

    def test_a_limit_above_the_total_changes_nothing(self):
        self.assertEqual(rules.dues_payments({"rome": 20.0}, 1000.0), [("rome", 20.0)])

    def test_a_limit_of_nothing_pays_nobody(self):
        self.assertEqual(rules.dues_payments({"rome": 20.0}, 0.0), [])

    def test_a_holder_owed_nothing_is_not_paid(self):
        self.assertEqual(rules.dues_payments({"rome": 0.0}, None), [])


class PayRouteDuesCommand(unittest.TestCase):
    """`Freight.pay_route_dues` on plain views: who holds the tiles, the carriers' wage, where each holder's dues go."""

    def freight(self, owners):
        return module_harness.build(Freight, views={
            **land_views.of({}, ("carriage_facts",)), "wage": lambda trade: WAGE, "tile_owner": owners,
            "holder_treasury": lambda holder: "government:" + holder})

    def test_the_payer_pays_each_holder_its_dues_into_the_holders_treasury(self):
        module = self.freight({"a": "rome", "b": "carthage"})
        paid = module.pay_route_dues(PayRouteDues("trader", ROUTE, 10.0))
        per_tonne = rules.dues_money_per_tonne(dues_hours_per_tonne(), WAGE)
        self.assertEqual(module_harness.sent(module), [
            PayActor("trader", "government:carthage", per_tonne["sail"] * 10.0, DUES_CAUSE),
            PayActor("trader", "government:rome", per_tonne["river_boat"] * 10.0, DUES_CAUSE)])
        self.assertEqual(paid, (per_tonne["sail"] + per_tonne["river_boat"]) * 10.0)

    def test_the_limit_caps_the_money_paid(self):
        module = self.freight({"a": "rome", "b": "carthage"})
        self.assertAlmostEqual(module.pay_route_dues(PayRouteDues("trader", ROUTE, 10.0, limit=5.0)), 5.0)
        self.assertAlmostEqual(sum(command.amount for command in module_harness.sent(module)), 5.0)

    def test_a_route_over_untaken_tiles_pays_nothing(self):
        module = self.freight(lambda tile: None)
        self.assertEqual(module.pay_route_dues(PayRouteDues("trader", ROUTE, 10.0)), 0.0)
        self.assertEqual(module_harness.sent(module), [])


class Cargo(TradeView):
    """The real trade view over a sim that holds partners' routes and pays dues for them."""

    def __init__(self, facts, dues_paid):
        self.needs = fake_needs(
            {PayRouteDues: lambda command: dues_paid(command.route, command.tonnes, command.limit)},
            civilisation={"id": "home"}, partner_facts=facts.get)


class PartnerCargo(unittest.TestCase):

    def test_the_dues_of_a_partner_route_are_limited_to_that_routes_freight(self):
        asked = []
        facts = {"han": {"route": ROUTE, "freight_per_tonne": 4.0}}
        cargo = Cargo(facts, lambda route, tonnes, limit: asked.append((route, tonnes, limit)) or 7.0)
        paid = cargo.pay_route_dues(PAYER, "home", "han", "grain", 10.0)
        self.assertEqual(asked, [(ROUTE, 10.0, 40.0)])
        self.assertEqual(paid, 7.0)

    def test_a_partner_with_no_route_pays_nothing(self):
        cargo = Cargo({"han": {"route": None, "freight_per_tonne": 4.0}}, lambda route, tonnes, limit: 99.0)
        self.assertEqual(cargo.pay_route_dues(PAYER, "home", "han", "grain", 10.0), 0.0)

    def test_a_cargo_that_goes_nowhere_pays_nothing(self):
        self.assertEqual(Cargo({}, lambda route, tonnes, limit: 99.0).pay_route_dues(PAYER, "home", "home", "grain", 10.0), 0.0)

    def test_both_ends_pay_when_neither_is_home(self):
        asked = []
        facts = {"han": {"route": ROUTE, "freight_per_tonne": 4.0}, "norse": {"route": ROUTE, "freight_per_tonne": 6.0}}
        cargo = Cargo(facts, lambda route, tonnes, limit: asked.append(limit) or 1.0)
        self.assertEqual(cargo.pay_route_dues(PAYER, "han", "norse", "grain", 10.0), 2.0)
        self.assertEqual(asked, [40.0, 60.0])


if __name__ == "__main__":
    unittest.main()
