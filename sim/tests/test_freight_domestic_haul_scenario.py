"""SCENARIO (Complaints/326): in a real game a domestic haul pays the mode's dues, the opposite flow makes the return cheaper,
and live stock is driven at the cost of its own feed. The geography and economy rules are in test_freight_domestic_haul."""

import unittest

from sim.geography import api as geography
from sim.geography import freight_cost
from sim.geography.api import dues_hours_per_tonne

LAND_ONLY_TILE = "chad_08"


class DomesticHaul(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from . import harness
        cls.game = harness.unopened_sim()

    def setUp(self):
        self.game.state.economy.agent_economy.pop("record", None)

    def test_a_domestic_cart_haul_pays_the_modes_dues(self):
        game = self.game
        wage = game.labour.wage_per_hour(game.FREIGHT_DRIVER_WAGE_TRADE)
        self.assertAlmostEqual(game.domestic_haul_dues_per_tonne("cart"), dues_hours_per_tonne()["cart"] * wage)
        self.assertGreater(game.domestic_haul_dues_per_tonne("cart"), 0.0)

    def _haul(self, cargo="goods", imbalance=None):
        game = self.game
        return game._haul_route([LAND_ONLY_TILE], game._domestic_flow_imbalance() if imbalance is None else imbalance, cargo)

    def test_a_land_haul_is_the_cart_rate_over_its_legs_plus_dues(self):
        game = self.game
        route = self._haul()
        self.assertEqual({leg.mode for leg in route.legs}, {"cart"})
        floor = sum(game.land_freight_money_per_tonne_km() * leg.distance_km for leg in route.legs)
        dues = game.domestic_haul_dues_per_tonne("cart")
        self.assertGreater(dues, 0.0)
        self.assertGreaterEqual(route.cost_per_tonne, floor + dues)

    def test_the_opposite_flow_makes_the_return_cheaper(self):
        game = self.game
        empty = self._haul().cost_per_tonne
        game.state.economy.agent_economy["record"] = {"carried": {"a": {"b": 10.0}, "b": {"a": 10.0}}}
        self.assertEqual(game._domestic_flow_imbalance(), 0.0)
        balanced = self._haul().cost_per_tonne
        self.assertLess(balanced, empty)

    def test_living_stock_is_driven_at_the_cost_of_its_own_feed(self):
        from sim.engine.living_stock_yearly import stock_rates
        game = self.game
        stock = sorted(stock_rates())[0]
        self.assertEqual(game._cargo_class(stock), "living_stock")
        self.assertEqual(game._cargo_class("iron_kg"), "goods")
        mode = game._domestic_haul_mode("living_stock")
        self.assertEqual(mode, "drove")
        driven, carted = self._haul("living_stock"), self._haul("goods")
        self.assertEqual({leg.mode for leg in driven.legs}, {mode})
        self.assertNotEqual(driven.cost_per_tonne, carted.cost_per_tonne)
        inputs = game._carrier_models()[mode][0]
        feed_price = game._material_price_per_kg(game.FREIGHT_FEED_PRICE_MATERIAL) or 0.0
        wage = game.labour.wage_per_hour(game.FREIGHT_DRIVER_WAGE_TRADE)
        floor = driven.distance_km * inputs.feed_kg_per_tonne_km * feed_price
        self.assertGreater(driven.cost_per_tonne, floor)
        self.assertEqual(game._carrier_models()[mode][1], freight_cost.CarrierPrices(0.0))
        self.assertGreater(wage, 0.0)

    def test_the_cargo_share_counts_a_herds_loss_on_the_road(self):
        from sim.engine.foreign_routes import Leg, Route
        from sim.engine.living_stock_yearly import stock_rates
        game = self.game
        stock = sorted(stock_rates())[0]
        mode_loss = geography.cargo_loss_per_day()["drove"]
        days = 400.0 / game._carrier_models()["drove"][0].distance_per_day_km
        route = Route((Leg("a", "b", "drove", 400.0, 0.0, days),))
        with_loss = game.domestic_cargo_cost_share(stock, route)
        interest_only = game.market_rate() * days / 365.0
        self.assertGreater(mode_loss, 0.0)
        self.assertGreater(with_loss, interest_only)

    def test_goods_modes_for_the_economy_leave_out_the_drove(self):
        costs = self.game._freight_mode_costs(cargo="goods")
        self.assertNotIn("drove", costs)
        self.assertIn("cart", costs)
        self.assertIn("drove", self.game._freight_mode_costs())

    def test_a_partner_route_for_stock_uses_the_stock_modes(self):
        from sim.engine.living_stock_yearly import stock_rates
        game = self.game
        goods_route = object()
        self.assertIs(game._material_route({}, "iron_kg", goods_route), goods_route)
        stock = sorted(stock_rates())[0]
        called = []
        game._foreign_route = lambda civilization, imbalance=None, cargo="goods": called.append(cargo) or "stock route"
        self.assertEqual(game._material_route({}, stock, goods_route), "stock route")
        self.assertEqual(called, ["living_stock"])


if __name__ == "__main__":
    unittest.main()
