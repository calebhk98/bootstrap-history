"""How a society's own figures reach foreign freight and the coin that pays for it (Complaints/326, 323): each method is
called on a stand-in that holds only what it reads. The carrier's physics is in test_foreign_freight_balance, the domestic
haul in test_freight_domestic_haul."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.engine import foreign_routes
from sim.engine.domestic_haul import DomesticHaulMixin
from sim.engine.foreign_payments import ForeignPaymentsMixin
from sim.engine.foreign_routes import ForeignRoutesMixin
from sim.geography import freight_cost, transport

CART = transport.draught_freight_physical_inputs(transport.OX, 2, transport.CART, transport.DIRT_TRACK)
SAIL_INPUTS = CART
PRICES = freight_cost.CarrierPrices(vehicle=100.0, animals=2000.0)
LAND_WAGE, SEA_WAGE = 1.0, 3.0


def freight_game(rate=0.1):
    return SimpleNamespace(
        FREIGHT_DRIVER_WAGE_TRADE="driver",
        labour=SimpleNamespace(wage_per_hour=lambda trade: LAND_WAGE if trade == "driver" else SEA_WAGE),
        market_rate=lambda: rate, world_map=None,
        _material_price_per_kg=lambda material: 0.5, _carrier_feed_material=lambda mode: "feed",
        _carrier_models=lambda: {"cart": (CART, PRICES, 250.0, 0.0), "sail": (SAIL_INPUTS, PRICES, 250.0, 0.0),
                                 "drove": (CART, freight_cost.CarrierPrices(0.0), 250.0, 0.0)})


def mode_costs(game, **kwargs):
    with mock.patch.object(foreign_routes, "walking_cargo_modes", return_value=["drove"]), \
         mock.patch.object(foreign_routes, "modes_carrying", return_value=["cart", "sail"]), \
         mock.patch.object(foreign_routes, "SEA_MODE", "sail"):
        return ForeignRoutesMixin._freight_mode_costs(game, **kwargs)


class FreightModeCostTests(unittest.TestCase):
    def test_every_mode_pays_its_return_leg_when_flows_are_one_sided(self):
        game = freight_game()
        balanced, one_sided = mode_costs(game, imbalance=0.0), mode_costs(game, imbalance=1.0)
        self.assertTrue(all(one_sided[mode] > balanced[mode] for mode in balanced), (balanced, one_sided))

    def test_dearer_money_in_this_society_raises_a_carriers_freight_but_not_a_herds_capital(self):
        cheap, dear = mode_costs(freight_game(0.1), imbalance=0.0), mode_costs(freight_game(0.4), imbalance=0.0)
        self.assertGreater(dear["cart"], cheap["cart"])
        self.assertEqual(dear["drove"], cheap["drove"])

    def test_the_sea_pays_the_crews_wage_and_land_the_drivers(self):
        costs = mode_costs(freight_game(), imbalance=0.0)
        self.assertGreater(costs["sail"], costs["cart"])

    def test_only_the_modes_asked_for_are_priced(self):
        self.assertEqual(sorted(mode_costs(freight_game(), imbalance=0.0, modes=("cart",))), ["cart"])

    def test_goods_modes_leave_out_a_mode_that_does_not_carry_the_cargo(self):
        self.assertEqual(sorted(mode_costs(freight_game(), imbalance=0.0, cargo="goods")), ["cart", "sail"])
        self.assertIn("drove", mode_costs(freight_game(), imbalance=0.0))


class FlowImbalanceTests(unittest.TestCase):
    def imbalance(self, book):
        game = SimpleNamespace(state=SimpleNamespace(economy=SimpleNamespace(foreign_market_book={"p": book})))
        return ForeignRoutesMixin._foreign_flow_imbalance(game, "p")

    def test_flows_that_match_are_balanced(self):
        self.assertEqual(self.imbalance({"iron": {"trade_tonnes": 10.0}, "cloth": {"trade_tonnes": -10.0}}), 0.0)

    def test_flow_one_way_is_fully_one_sided(self):
        self.assertEqual(self.imbalance({"iron": {"trade_tonnes": 10.0}}), 1.0)

    def test_no_book_is_fully_one_sided(self):
        self.assertEqual(self.imbalance({}), 1.0)


class RouteFreightTests(unittest.TestCase):
    def test_a_route_costs_what_its_route_says_and_no_route_is_infinite(self):
        game = SimpleNamespace(_foreign_route=lambda civilization, imbalance=None: SimpleNamespace(cost_per_tonne=12.0))
        self.assertEqual(ForeignRoutesMixin._route_freight_per_tonne(game, "p"), 12.0)
        game = SimpleNamespace(_foreign_route=lambda civilization, imbalance=None: None)
        self.assertEqual(ForeignRoutesMixin._route_freight_per_tonne(game, "p"), float("inf"))

    def test_the_imbalance_asked_for_reaches_the_route(self):
        asked = []
        game = SimpleNamespace(_foreign_route=lambda civilization, imbalance=None: asked.append(imbalance) or None)
        ForeignRoutesMixin._route_freight_per_tonne(game, "p", 0.5)
        self.assertEqual(asked, [0.5])


class DuesAndStockRouteTests(unittest.TestCase):
    def test_a_haul_pays_the_modes_dues_hours_at_the_carriers_wage(self):
        game = SimpleNamespace(_freight_handling_costs=lambda: {"cart": 6.0})
        self.assertEqual(DomesticHaulMixin.domestic_haul_dues_per_tonne(game, "cart"), 6.0)
        self.assertEqual(DomesticHaulMixin.domestic_haul_dues_per_tonne(game, "sail"), 0.0)

    def test_handling_costs_are_the_geographys_dues_hours_at_the_land_wage(self):
        game = SimpleNamespace(FREIGHT_DRIVER_WAGE_TRADE="driver", world_map=None,
                               labour=SimpleNamespace(wage_per_hour=lambda trade: 2.0))
        with mock.patch.object(foreign_routes, "dues_hours_per_tonne", return_value={"cart": 3.0}), \
             mock.patch.object(foreign_routes, "handling_money_per_tonne", lambda hours, wage, sea, port: {"cart": hours["cart"] * wage}):
            self.assertEqual(ForeignRoutesMixin._freight_handling_costs(game), {"cart": 6.0})

    def test_stock_takes_its_own_route_and_goods_the_one_already_found(self):
        asked = []
        game = SimpleNamespace(_cargo_class=lambda material: "goods" if material == "iron" else "living_stock",
                               _foreign_route=lambda civilization, imbalance=None, cargo="goods": asked.append(cargo) or "stock route")
        found = object()
        self.assertIs(DomesticHaulMixin._material_route(game, {}, "iron", found), found)
        self.assertEqual(DomesticHaulMixin._material_route(game, {}, "ox", found), "stock route")
        self.assertEqual(asked, ["living_stock"])


class SettleFlowTests(unittest.TestCase):
    OPENING = 1000.0

    def game(self, home_stock):
        ledger = {"goods_in_value": 0.0, "goods_out_value": 0.0, "home_coin_units": 0.0, "partner_coin_units": 0.0,
                  "coin_carriage_units": 0.0}
        return SimpleNamespace(
            _foreign_ledger=lambda civilization, create=False: ledger, _note_trade_value=lambda tonnes, value: None,
            home_coin_stock_units=lambda: home_stock + ledger["home_coin_units"],
            _partner_coin_opening_units=lambda civilization: self.OPENING,
            coin_carriage_units=lambda civilization, units, rate: 0.0), ledger

    def test_an_import_is_paid_in_coin_that_leaves_home_and_arrives_at_the_partner(self):
        game, ledger = self.game(home_stock=1000.0)
        ForeignPaymentsMixin._settle_flow(game, "p", 5.0, 100.0, 2.0)
        self.assertEqual((ledger["home_coin_units"], ledger["partner_coin_units"], ledger["goods_in_value"]),
                         (-100.0, 50.0, 100.0))

    def test_an_import_beyond_the_coin_held_is_paid_only_as_far_as_the_stock_goes(self):
        game, ledger = self.game(home_stock=30.0)
        ForeignPaymentsMixin._settle_flow(game, "p", 5.0, 100.0, 2.0)
        self.assertEqual((ledger["home_coin_units"], ledger["partner_coin_units"]), (-30.0, 15.0))

    def test_an_export_brings_coin_home_and_draws_it_from_the_partner(self):
        game, ledger = self.game(home_stock=1000.0)
        ForeignPaymentsMixin._settle_flow(game, "p", -5.0, 100.0, 2.0)
        self.assertEqual((ledger["home_coin_units"], ledger["partner_coin_units"], ledger["goods_out_value"]),
                         (100.0, -50.0, 100.0))


if __name__ == "__main__":
    unittest.main()
