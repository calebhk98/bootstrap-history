"""Complaints/416: the freight module's carrier models price a railway and a canal barge from freight physics, so the
agent economy can haul over a built railway or canal."""
QUICK_TOPIC = True

import unittest

from sim.freight.module import Freight
from sim.geography import api as geography
from sim.tests import module_harness

PRICES = {"wheat_kg": 1.0, "wood_kg": 0.5, "coal_kg": 0.4, "iron_bar_kg": 8.0, "ox": 4000.0, "mule": 3000.0}
WORLD_MAP = geography.open_map()


def _economy(prices=None):
    """The freight module over a price table, a flat wage, the market rate and the real map."""
    table = dict(PRICES, **(prices or {}))
    return module_harness.build(Freight, views={
        "material_prices": lambda: table, "material_price": lambda tag: table.get(tag), "wage": lambda trade: 2.0,
        "market_rate": lambda: 0.05, "legacy_world_map": lambda: WORLD_MAP})


class RailCarriageTests(unittest.TestCase):

    def test_the_carrier_models_hold_a_train_and_a_canal_barge(self):
        models = _economy().carrier_models()
        self.assertIn("rail", models)
        self.assertIn("canal", models)
        inputs = models["rail"][0]
        self.assertGreater(inputs.cargo_tonnes, 100.0)
        self.assertGreater(inputs.feed_kg_per_tonne_km, 0.0)

    def test_a_train_hauls_a_tonne_km_for_less_than_an_ox_cart(self):
        costs = _economy().freight_mode_costs(1.0)
        self.assertGreater(costs["rail"], 0.0)
        self.assertLess(costs["rail"], costs["cart"])

    def test_the_train_is_priced_with_its_fuel_not_with_feed(self):
        cheap = _economy({"coal_kg": 0.1}).freight_mode_costs(1.0)
        dear = _economy({"coal_kg": 4.0}).freight_mode_costs(1.0)
        self.assertGreater(dear["rail"], cheap["rail"])
        self.assertEqual(dear["cart"], cheap["cart"])
        base, wheat = _economy().freight_mode_costs(1.0), _economy({"wheat_kg": 9.0}).freight_mode_costs(1.0)
        self.assertEqual(wheat["rail"], base["rail"])
        self.assertGreater(wheat["cart"], base["cart"])

    def test_a_canal_barge_costs_what_a_river_barge_does_on_still_water(self):
        costs = _economy().freight_mode_costs(1.0)
        self.assertAlmostEqual(costs["canal"], costs["river_boat"])

    def test_an_empty_return_doubles_the_train_rate_but_not_its_weather_losses(self):
        economy = _economy()
        one_sided, balanced = economy.freight_mode_costs(1.0)["rail"], economy.freight_mode_costs(0.0)["rail"]
        self.assertAlmostEqual(one_sided, 2.0 * balanced)


if __name__ == "__main__":
    unittest.main()
