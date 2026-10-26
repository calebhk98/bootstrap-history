"""The freight module's plain rules (sim/freight/rules.py) on written-out inputs: the share of a mode's lift that arrives
as cargo, the provisioning rate a searched leg already carries, the share of cargo lost on a route, and the hands a hull
sails with."""
QUICK_TOPIC = True

import unittest

from sim.freight import rules
from sim.freight.route import Leg, Route
from sim.geography import freight_cost, provisions, sea_freight, transport

CART = transport.draught_freight_physical_inputs(transport.OX, 2, transport.CART, transport.DIRT_TRACK)
HULL = sea_freight.sailing_freight_physical_inputs()
MODELS = {"cart": (CART, freight_cost.CarrierPrices(vehicle=100.0, animals=2000.0), 250.0, 0.0),
          "sail": (HULL, freight_cost.CarrierPrices(vehicle=100.0), 150.0, 0.0)}


class RestockDays(unittest.TestCase):

    def test_a_hull_at_sea_does_not_restock_and_a_land_carrier_does(self):
        self.assertIsNone(rules.restock_days("sail"))
        self.assertEqual(rules.restock_days("cart"), provisions.RESTOCK_INTERVAL_DAYS)


class ShareInRate(unittest.TestCase):

    def test_a_searched_rate_over_the_base_rate_is_the_share_it_divides_by(self):
        self.assertAlmostEqual(rules.share_in_rate("cart", {"cart": 1.0}, {"cart": 2.0}), 0.5)

    def test_no_rates_or_an_unpassable_mode_divide_by_nothing(self):
        self.assertEqual(rules.share_in_rate("cart", None, {"cart": 2.0}), 1.0)
        self.assertEqual(rules.share_in_rate("cart", {"cart": 1.0}, {"cart": float("inf")}), 1.0)
        self.assertEqual(rules.share_in_rate("cart", {"cart": 0.0}, {"cart": 2.0}), 1.0)


class DeliveredShare(unittest.TestCase):

    def test_a_mode_without_a_carrier_model_delivers_all_of_its_lift(self):
        self.assertEqual(rules.delivered_share(MODELS, "teleport", None), 1.0)

    def test_with_no_route_yet_a_hull_delivers_all_and_a_land_carrier_its_stage(self):
        self.assertEqual(rules.delivered_share(MODELS, "sail", None), provisions.restocked_share(HULL, 0.0, None))
        self.assertEqual(rules.delivered_share(MODELS, "cart", None),
                         provisions.restocked_share(CART, float("inf"), provisions.RESTOCK_INTERVAL_DAYS))

    def test_the_mean_leg_of_the_mode_sets_the_share(self):
        route = Route((Leg("a", "b", "cart", 100.0, 1.0), Leg("b", "c", "sail", 900.0, 1.0), Leg("c", "d", "cart", 300.0, 1.0)))
        self.assertEqual(rules.delivered_share(MODELS, "cart", route),
                         provisions.restocked_share(CART, 200.0, provisions.RESTOCK_INTERVAL_DAYS))


class CargoLossShare(unittest.TestCase):

    def test_no_route_loses_nothing(self):
        self.assertEqual(rules.cargo_loss_share(None, {}, 0.01), 0.0)

    def test_a_land_route_of_modes_that_lose_nothing_loses_nothing_at_sea_or_on_the_road(self):
        route = Route((Leg("a", "b", "cart", 100.0, 1.0, 5.0),))
        self.assertEqual(rules.cargo_loss_share(route, {}, 0.01), 0.0)

    def test_sea_legs_lose_by_the_hull_rate_over_the_kilometres_sailed(self):
        sea = Route((Leg("a", "b", "sail", 2000.0, 1.0, 20.0),))
        longer = Route((Leg("a", "b", "sail", 4000.0, 1.0, 40.0),))
        self.assertGreater(rules.cargo_loss_share(sea, {}, 0.01), 0.0)
        self.assertGreater(rules.cargo_loss_share(longer, {}, 0.01), rules.cargo_loss_share(sea, {}, 0.01))

    def test_a_herd_on_the_road_adds_its_daily_loss_to_the_sea_loss(self):
        route = Route((Leg("a", "b", "sail", 2000.0, 1.0, 20.0), Leg("b", "c", "drove", 100.0, 1.0, 10.0)))
        self.assertGreater(rules.cargo_loss_share(route, {"drove": 0.01}, 0.01), rules.cargo_loss_share(route, {}, 0.01))


class SeaCrew(unittest.TestCase):

    def test_the_rig_crew_is_the_floor_and_a_dearer_cargo_hires_more_defenders(self):
        rig = sea_freight.crew_to_sail(HULL.cargo_tonnes)
        cheap = rules.sea_crew_hands(1.0, 0.001, 0.5)
        dear = rules.sea_crew_hands(1.0, 100.0, 0.5)
        self.assertGreaterEqual(cheap, rig)
        self.assertGreater(dear, cheap)


class FlowImbalance(unittest.TestCase):

    def test_a_partner_taking_less_than_it_sends_leaves_the_return_part_empty(self):
        entries = [{"trade_tonnes": 30.0}, {"trade_tonnes": -10.0}]
        self.assertAlmostEqual(rules.foreign_flow_imbalance(entries), freight_cost.imbalance_of_flows(30.0, 10.0))


if __name__ == "__main__":
    unittest.main()
