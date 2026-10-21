"""Complaint 568: the cheapest route over the map prices each leg at its own mode's rate, with the dues of the
mode once, through the one route search foreign trade and domestic hauls share. Rates here are given, not a game's."""

QUICK_TOPIC = True

import unittest

from sim.engine.data import load_civ
from sim.geography.api import route as route_search, tiles_held

SEA_TILE = "india_01"
LAND_TILE = "chad_08"
MIXED_TILE = "mongolia_01"
HELD = {"sea_square_sail", "lnd_ox_transport", "lnd_two_wheel_cart"}
RATES = {"sail": 1.0, "river_boat": 5.0, "cart": 100.0}
HANDLING = {"sail": 7.0, "cart": 2.0}


def _haul(origin):
    return route_search([origin], tiles_held(load_civ("rome_100ad")), list(RATES), mode_costs=RATES,
                        handling_costs=HANDLING, held_nodes=HELD)


class RouteLegsAtTheirOwnRates(unittest.TestCase):

    def test_a_sea_route_costs_the_sail_rate_over_its_length_plus_port_handling_once(self):
        route = _haul(SEA_TILE)
        self.assertEqual({leg["mode"] for leg in route["legs"]}, {"sail"})
        self.assertAlmostEqual(route["cost_per_tonne"], RATES["sail"] * route["km"] + HANDLING["sail"], delta=1e-6)
        self.assertLess(route["cost_per_tonne"] / route["km"], 0.1 * RATES["cart"])

    def test_a_land_route_is_the_cart_rate_over_every_leg_plus_dues(self):
        route = _haul(LAND_TILE)
        self.assertEqual({leg["mode"] for leg in route["legs"]}, {"cart"})
        self.assertGreaterEqual(route["cost_per_tonne"], RATES["cart"] * route["km"] + HANDLING["cart"])

    def test_a_mixed_route_charges_each_leg_its_own_mode(self):
        route = _haul(MIXED_TILE)
        self.assertGreater(len({leg["mode"] for leg in route["legs"]}), 1)
        for leg in route["legs"]:
            per_km = leg["cost_per_tonne"] / leg["km"]
            if leg["mode"] == "cart":
                self.assertGreaterEqual(per_km, RATES["cart"] - 1e-9)
            elif leg["mode"] in ("sail", "river_boat"):
                self.assertLess(per_km, RATES["cart"])

    def test_a_dearer_cart_rate_makes_a_dearer_land_route(self):
        dearer = route_search([LAND_TILE], tiles_held(load_civ("rome_100ad")), ["cart"], mode_costs={"cart": 200.0},
                              handling_costs=HANDLING, held_nodes=HELD)
        self.assertGreater(dearer["cost_per_tonne"], _haul(LAND_TILE)["cost_per_tonne"])


if __name__ == "__main__":
    unittest.main()
