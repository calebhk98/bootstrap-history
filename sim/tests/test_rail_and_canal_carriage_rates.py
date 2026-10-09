"""Complaints/416: the engine's carrier models price a railway and a canal barge from freight physics, so the
agent economy can haul over a built railway or canal."""
QUICK_TOPIC = True

import unittest

from sim.engine import foreign_routes
from sim.geography import api as geography
from sim.geography.api import transport as freight_physics

PRICES = {"wheat_kg": 1.0, "wood_kg": 0.5, "coal_kg": 0.4, "iron_bar_kg": 8.0, "ox": 4000.0, "mule": 3000.0}


class _Labour:
    def wage_per_hour(self, trade):
        return 2.0


class _Economy(foreign_routes.ForeignRoutesMixin):
    LAND_FREIGHT_TEAM_SIZE = 2.0
    FREIGHT_FEED_PRICE_MATERIAL = "wheat_kg"
    FREIGHT_DRIVER_WAGE_TRADE = "labourer"

    def __init__(self, prices=None):
        self.prices = dict(PRICES, **(prices or {}))
        self.labour = _Labour()
        self.world_map = geography.open_map()

    def _material_prices(self):
        return self.prices

    def _material_price_per_kg(self, tag):
        return self.prices.get(tag)

    def _land_freight_physical_inputs(self):
        return freight_physics.draught_freight_physical_inputs(
            freight_physics.OX, 2, freight_physics.CART, freight_physics.DIRT_TRACK)

    def market_rate(self):
        return 0.05


class RailCarriageTests(unittest.TestCase):

    def test_the_carrier_models_hold_a_train_and_a_canal_barge(self):
        models = _Economy()._carrier_models()
        self.assertIn("rail", models)
        self.assertIn("canal", models)
        inputs = models["rail"][0]
        self.assertGreater(inputs.cargo_tonnes, 100.0)
        self.assertGreater(inputs.feed_kg_per_tonne_km, 0.0)

    def test_a_train_hauls_a_tonne_km_for_less_than_an_ox_cart(self):
        costs = _Economy()._freight_mode_costs(1.0)
        self.assertGreater(costs["rail"], 0.0)
        self.assertLess(costs["rail"], costs["cart"])

    def test_the_train_is_priced_with_its_fuel_not_with_feed(self):
        cheap = _Economy({"coal_kg": 0.1})._freight_mode_costs(1.0)
        dear = _Economy({"coal_kg": 4.0})._freight_mode_costs(1.0)
        self.assertGreater(dear["rail"], cheap["rail"])
        self.assertEqual(dear["cart"], cheap["cart"])
        base, wheat = _Economy()._freight_mode_costs(1.0), _Economy({"wheat_kg": 9.0})._freight_mode_costs(1.0)
        self.assertEqual(wheat["rail"], base["rail"])
        self.assertGreater(wheat["cart"], base["cart"])

    def test_a_canal_barge_costs_what_a_river_barge_does_on_still_water(self):
        costs = _Economy()._freight_mode_costs(1.0)
        self.assertAlmostEqual(costs["canal"], costs["river_boat"])

    def test_an_empty_return_doubles_the_train_rate_but_not_its_weather_losses(self):
        economy = _Economy()
        one_sided, balanced = economy._freight_mode_costs(1.0)["rail"], economy._freight_mode_costs(0.0)["rail"]
        self.assertAlmostEqual(one_sided, 2.0 * balanced)


if __name__ == "__main__":
    unittest.main()
