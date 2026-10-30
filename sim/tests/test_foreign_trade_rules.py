"""The foreign-trade module's rules: how a flow is paid in coin, how much a route's carriers lift, how a cargo leg is kept and
settled, and which book entries a partner opens. The rules are plain functions called on written-out values; the module's
own methods run over plain views (`module_harness`)."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.foreign_trade import rules
from sim.foreign_trade.commands import SettleFlow
from sim.foreign_trade.module import ForeignTrade
from sim.foreign_trade.state import ForeignTradeWorld
from sim.tests import module_harness


class PaymentRules(unittest.TestCase):
    def test_an_import_is_paid_in_coin_from_the_home_stock_and_received_in_the_partners_units(self):
        self.assertEqual(rules.import_payment(100.0, 1000.0, 2.0), (100.0, 50.0))

    def test_an_import_beyond_the_coin_held_is_paid_only_as_far_as_the_stock_goes(self):
        self.assertEqual(rules.import_payment(100.0, 30.0, 2.0), (30.0, 15.0))

    def test_an_export_is_paid_by_the_partner_never_beyond_what_it_holds(self):
        self.assertEqual(rules.export_payment(100.0, 1000.0, 2.0), 50.0)
        self.assertEqual(rules.export_payment(100.0, 20.0, 2.0), 20.0)

    def test_the_carriers_keep_their_pay_at_home_when_coin_is_carried_in(self):
        ledger = rules.blank_ledger()
        rules.book_import(ledger, 100.0, 50.0, 5.0, 2.0)
        self.assertEqual((ledger["home_coin_units"], ledger["partner_coin_units"], ledger["coin_carriage_units"]),
                         (-90.0, 45.0, 5.0))

    def test_an_export_brings_coin_home_and_the_carriage_is_booked(self):
        ledger = rules.blank_ledger()
        rules.book_export(ledger, 50.0, 5.0, 2.0)
        self.assertEqual((ledger["home_coin_units"], ledger["coin_carriage_units"]), (100.0, 5.0))

    def test_only_the_last_few_years_of_trade_value_are_kept(self):
        by_year = {}
        for year in (100, 101, 102, 103):
            rules.note_trade_value(by_year, year, 1.0, 10.0)
        rules.note_trade_value(by_year, 103, -1.0, 4.0)
        self.assertEqual(by_year, {"101": {"in": 10.0, "out": 0.0}, "102": {"in": 10.0, "out": 0.0}, "103": {"in": 10.0, "out": 4.0}})


class LiftRules(unittest.TestCase):
    CART = SimpleNamespace(cargo_tonnes=2.0)

    def test_a_legs_lift_is_a_round_trip_with_the_cargo_one_way(self):
        self.assertEqual(rules.lift_years_per_tonne(2.0, 100.0, 10.0), 0.1)

    def test_the_lift_years_of_a_route_add_over_its_legs_and_a_route_of_no_legs_has_none(self):
        self.assertEqual(rules.route_lift_years_per_tonne([(self.CART, 100.0, 10.0), (self.CART, 50.0, 5.0)]), 0.1 + 0.1)
        self.assertIsNone(rules.route_lift_years_per_tonne([]))

    def test_the_capital_of_a_routes_lift_is_the_carriers_it_needs_priced(self):
        prices = SimpleNamespace(vehicle=100.0, animals=20.0)
        self.assertEqual(rules.route_capital_per_lift_tonne([(self.CART, prices, 100.0, 10.0)]), 0.1 * 120.0)

    def test_a_route_with_no_legs_lifts_without_limit_and_others_open_with_the_carriers_the_ledger_has_not_yet_grown(self):
        self.assertEqual(rules.lift_capacity(None, 0.0, 10.0), float("inf"))
        self.assertEqual(rules.lift_capacity(0.5, 0.0, 10.0), 20.0)
        self.assertEqual(rules.lift_capacity(0.5, 7.0, 10.0), 7.0)

    def test_the_lift_left_this_year_is_what_the_year_has_not_used(self):
        ledger = dict(rules.blank_ledger(), lift_year=100, lift_used_in=6.0, lift_used_out=12.0)
        self.assertEqual(rules.lift_left(ledger, 100, 10.0), (4.0, 0.0))
        self.assertEqual(rules.lift_left(ledger, 101, 10.0), (10.0, 10.0))


class CargoRules(unittest.TestCase):
    def test_a_cargo_into_home_is_a_landing_out_of_it_a_taking_and_between_partners_a_through_leg(self):
        self.assertEqual(rules.cargo_kind("home", "han", "home"), ("in", "han"))
        self.assertEqual(rules.cargo_kind("han", "home", "home"), ("out", "han"))
        self.assertEqual(rules.cargo_kind("persia", "han", "home"), ("through", "persia"))

    def test_a_landing_leg_is_paid_to_the_partner_and_trued_up_to_what_the_book_gave(self):
        leg = {"kind": "in", "tonnes": 10.0, "partner": "han", "paid": 100.0, "received": 160.0}
        self.assertEqual(rules.leg_settlement(leg, {"tonnes": 8.0, "money": 120.0}), (None, [("han", 10.0, 100.0)], -40.0))

    def test_a_taking_leg_the_book_part_filled_is_paid_in_part_and_the_rest_comes_off_the_partners_tally(self):
        leg = {"kind": "out", "tonnes": 10.0, "partner": "han", "paid": 100.0, "received": 160.0}
        taken_back, payments, delta = rules.leg_settlement(leg, {"tonnes": 6.0, "money": 30.0})
        self.assertAlmostEqual(taken_back, -4.0)
        self.assertEqual(payments[0][:2], ("han", -6.0))
        self.assertAlmostEqual(payments[0][2], 96.0)
        self.assertAlmostEqual(delta, -34.0)


class ModuleBooks(unittest.TestCase):
    def module(self, **views):
        return module_harness.build(ForeignTrade, world=ForeignTradeWorld(), views=dict({"year": 100}, **views))

    def test_reading_a_partners_ledger_creates_nothing_and_a_settlement_creates_it(self):
        module = self.module()
        self.assertEqual(module.foreign_coin_partner_units("han"), 0.0)
        self.assertEqual(module.world.ledgers, {})
        module.ledger_of("han", create=True)
        self.assertEqual(list(module.world.ledgers), ["han"])

    def test_the_coin_home_is_summed_over_every_partner_ledger(self):
        module = self.module()
        module.world.ledgers.update({"han": dict(rules.blank_ledger(), home_coin_units=3.0),
                                     "persia": dict(rules.blank_ledger(), home_coin_units=-1.0)})
        self.assertEqual(module.foreign_coin_home_units(), 2.0)

    def test_a_flow_is_settled_in_the_partners_coin_and_noted_in_the_years_trade_value(self):
        module = self.module(home_coin_stock=1000.0, partner_coin_opening=lambda partner: 500.0,
                             coin_carriage_units=lambda partner, units, rate: 0.0,
                             home_unit_price=lambda metal: 2.0, civilisation_record=lambda partner: {
                                 "coin_standard": {"material": "silver_kg", "kg_per_unit": 1.0}})
        module.apply_settle_flow(SettleFlow("han", 5.0, 100.0))
        self.assertEqual(module.world.ledgers["han"]["goods_in_value"], 100.0)
        self.assertEqual(module.trade_value_in_year(100), {"in": 100.0, "out": 0.0})

    def test_a_flow_is_not_settled_while_the_partners_coin_metal_has_no_home_price(self):
        module = self.module(home_unit_price=lambda metal: None, civilisation_record=lambda partner: {
            "coin_standard": {"material": "silver_kg", "kg_per_unit": 1.0}})
        module.apply_settle_flow(SettleFlow("han", 5.0, 100.0))
        self.assertEqual((module.world.ledgers, module.world.trade_by_year), ({}, {}))

    def test_the_first_recorded_lift_fixes_the_routes_yearly_capacity_and_uses_it(self):
        module = self.module(carrier_models=lambda: {})
        module.record_lift("han", None, 4.0, 1.0)
        ledger = module.world.ledgers["han"]
        self.assertEqual((ledger["lift_year"], ledger["lift_used_in"], ledger["lift_unmet"]), (100, 4.0, 1.0))
        self.assertEqual(ledger["lift_tonnes_per_year"], float("inf"))   # no legs: no limit

    def test_a_partners_book_entry_opens_on_first_use_only_where_it_wants_the_good(self):
        class Opens(ForeignTrade):
            def foreign_opening(self, partner, commodity, solved):
                return (5.0, 8.0) if commodity == "grain" else (0.0, 0.0)
        module = module_harness.build(Opens, world=ForeignTradeWorld())
        entry = module.partner_entry("han", "grain", {"solved_materials": ()})
        self.assertEqual(entry, {"reference_tonnes": 8.0, "capacity_tonnes": 5.0, "stock_tonnes": 0.0,
                                 "price_ratio": 1.0, "trade_tonnes": 0.0})
        self.assertIs(module.partner_entry("han", "grain", {"solved_materials": ()}), entry)
        self.assertIsNone(module.partner_entry("han", "iron", {"solved_materials": ()}))
        self.assertEqual(list(module.world.market_book["han"]), ["grain"])


if __name__ == "__main__":
    unittest.main()
