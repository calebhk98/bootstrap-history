"""Complaint 568: a material's carriage prices the cheapest route leg by leg, each leg at its own mode's rate,
with the dues of each change of mode, through the one haul function foreign trade uses."""

QUICK_TOPIC = False

import unittest

from sim.engine import action_results
from sim.engine.data import load_civ
from sim.geography.api import tiles_held
from sim.tests import harness

SEA_TILE = "india_01"
LAND_TILE = "chad_08"
MIXED_TILE = "mongolia_01"
LOCATED_GOOD = "pozzolana_kg"


class MaterialHaulLegs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.game = harness.unopened_sim()
        cls.imbalance = cls.game._domestic_flow_imbalance()
        cls.rates = cls.game._freight_mode_costs(cls.imbalance)

    def _haul(self, tile):
        return self.game._haul_route([tile], self.imbalance, "goods")

    def test_a_sea_route_costs_the_sail_rate_plus_port_handling(self):
        route = self._haul(SEA_TILE)
        self.assertEqual({leg.mode for leg in route.legs}, {"sail"})
        handling = self.game._freight_handling_costs()["sail"]
        self.assertGreater(handling, 0.0)
        self.assertAlmostEqual(route.cost_per_tonne, self.rates["sail"] * route.distance_km + handling,
                               delta=0.01 * route.cost_per_tonne)
        self.assertLess(route.cost_per_tonne / route.distance_km, 0.1 * self.rates["cart"])

    def test_a_land_route_is_the_cart_rate_over_every_leg_plus_dues(self):
        route = self._haul(LAND_TILE)
        self.assertEqual({leg.mode for leg in route.legs}, {"cart"})
        dues = self.game.domestic_haul_dues_per_tonne("cart")
        self.assertGreater(dues, 0.0)
        self.assertGreaterEqual(route.cost_per_tonne, self.rates["cart"] * route.distance_km + dues)

    def test_a_mixed_route_charges_each_leg_its_own_mode(self):
        route = self._haul(MIXED_TILE)
        self.assertGreater(len({leg.mode for leg in route.legs}), 1)
        for leg in route.legs:
            per_km = leg.cost_per_tonne / leg.distance_km
            if leg.mode == "cart":
                self.assertGreaterEqual(per_km, self.rates["cart"] - 1e-9)
            elif leg.mode in ("sail", "river_boat"):
                self.assertLess(per_km, self.rates["cart"])

    def test_domestic_and_foreign_hauls_share_the_one_function(self):
        game = self.game
        partner = load_civ("han_china_100ad")
        foreign = game._foreign_route("han_china_100ad", 1.0)
        direct = game._haul_route(tiles_held(partner, game.world_map), 1.0, "goods",
                                  partner_techs=action_results.expand(game.nodes, frozenset(partner.get("starting_techs") or ())))
        self.assertEqual(foreign.legs, direct.legs)


class LocatedMaterialCarriage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.game = harness.unopened_sim(civ="norse_900ad")

    def test_carriage_is_the_routes_cost_not_one_land_rate_over_its_length(self):
        game = self.game
        route = game.material_haul_route(LOCATED_GOOD)
        self.assertIn("sail", {leg.mode for leg in route.legs})
        self.assertAlmostEqual(game.material_carriage_per_tonne(LOCATED_GOOD, 0.0), route.cost_per_tonne)
        cart_rate = game.land_freight_money_per_tonne_km(game._domestic_flow_imbalance())
        self.assertLess(route.cost_per_tonne, 0.1 * cart_rate * route.distance_km)

    def test_a_tracked_mineral_far_away_is_carried_by_its_route(self):
        game = self.game
        route = game.material_haul_route("saltpetre")
        self.assertIn("sail", {leg.mode for leg in route.legs})
        cart_rate = game.land_freight_money_per_tonne_km(game._domestic_flow_imbalance())
        self.assertLess(route.cost_per_tonne, 0.1 * cart_rate * route.distance_km)

    def test_a_material_made_on_held_ground_costs_nothing_to_carry(self):
        holder = harness.unopened_sim()
        self.assertEqual(holder.material_haul_route(LOCATED_GOOD).legs, ())
        self.assertEqual(holder.material_carriage_per_tonne(LOCATED_GOOD, 100.0), 0.0)


if __name__ == "__main__":
    unittest.main()
