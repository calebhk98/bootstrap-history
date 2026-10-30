"""How a society's own figures reach foreign freight and the coin that pays for it (Complaints/326, 323): the freight module's
mode costs, handling costs and route quotes on plain views and a written-out carrier table, the flow imbalance as a rule,
(the coin settlement is in test_foreign_trade_rules). The carrier's physics is in test_foreign_freight_balance,
the domestic haul in test_freight_domestic_haul."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.freight import rules
from sim.freight.module import Freight
from sim.geography import freight_cost, transport
from sim.tests import module_harness

CART = transport.draught_freight_physical_inputs(transport.OX, 2, transport.CART, transport.DIRT_TRACK)
SAIL_INPUTS = CART
PRICES = freight_cost.CarrierPrices(vehicle=100.0, animals=2000.0)
LAND_WAGE, SEA_WAGE = 1.0, 3.0


class _Carriers(Freight):
    """The freight module with its carrier table written out."""

    def carrier_models(self):
        return {"cart": (CART, PRICES, 250.0, 0.0), "sail": (SAIL_INPUTS, PRICES, 250.0, 0.0),
                "drove": (CART, freight_cost.CarrierPrices(0.0), 250.0, 0.0)}

    def carrier_feed_material(self, mode):
        return "feed"


def freight_game(rate=0.1, implementation=_Carriers):
    return module_harness.build(implementation, views={
        "wage": lambda trade: SEA_WAGE if trade == "sailor" else LAND_WAGE, "market_rate": lambda: rate,
        "carriage_facts": lambda: {"walking_modes": ["drove"], "loss_per_day": {}, "dues_hours_per_tonne": {}},
        "modes_carrying": lambda cargo: ["cart", "sail"], "material_price": lambda material: 0.5})


def mode_costs(game, **kwargs):
    return game.freight_mode_costs(**kwargs)


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
        return rules.foreign_flow_imbalance(book.values())

    def test_flows_that_match_are_balanced(self):
        self.assertEqual(self.imbalance({"iron": {"trade_tonnes": 10.0}, "cloth": {"trade_tonnes": -10.0}}), 0.0)

    def test_flow_one_way_is_fully_one_sided(self):
        self.assertEqual(self.imbalance({"iron": {"trade_tonnes": 10.0}}), 1.0)

    def test_no_book_is_fully_one_sided(self):
        self.assertEqual(self.imbalance({}), 1.0)


class RouteFreightTests(unittest.TestCase):
    def test_a_route_costs_what_its_route_says_and_no_route_is_infinite(self):
        class Found(Freight):
            def foreign_route(self, civilization, imbalance=None, cargo="goods"):
                return SimpleNamespace(cost_per_tonne=12.0)

        class NotFound(Freight):
            def foreign_route(self, civilization, imbalance=None, cargo="goods"):
                return None
        self.assertEqual(module_harness.build(Found).route_freight_per_tonne({"id": "p"}), 12.0)
        self.assertEqual(module_harness.build(NotFound).route_freight_per_tonne({"id": "p"}), float("inf"))

    def test_the_imbalance_asked_for_reaches_the_route(self):
        asked = []

        class Asked(Freight):
            def foreign_route(self, civilization, imbalance=None, cargo="goods"):
                asked.append(imbalance)
        module_harness.build(Asked).route_freight_per_tonne({"id": "p"}, 0.5)
        self.assertEqual(asked, [0.5])


class DuesAndStockRouteTests(unittest.TestCase):
    def test_handling_costs_are_the_geographys_dues_hours_at_the_land_wage(self):
        game = freight_game()
        game.needs.carriage_facts = lambda: {"walking_modes": [], "loss_per_day": {}, "dues_hours_per_tonne": {"cart": 3.0}}
        with mock.patch.object(rules, "handling_money_per_tonne", lambda hours, wage, sea, port: {"cart": hours["cart"] * wage}):
            self.assertEqual(game.freight_handling_costs(), {"cart": 3.0 * LAND_WAGE})

    def test_stock_takes_its_own_route_and_goods_the_one_already_found(self):
        asked = []

        class Routed(Freight):
            def cargo_class(self, material):
                return "goods" if material == "iron" else "living_stock"

            def foreign_route(self, civilization, imbalance=None, cargo="goods"):
                asked.append(cargo)
                return "stock route"
        module, found = module_harness.build(Routed), object()
        self.assertIs(module.material_route({}, "iron", found), found)
        self.assertEqual(module.material_route({}, "ox", found), "stock route")
        self.assertEqual(asked, ["living_stock"])


if __name__ == "__main__":
    unittest.main()
