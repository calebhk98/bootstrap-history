"""Heavy cheap goods move a few days by land and far by sea because the carrier's own needs eat the
cargo's value (Complaint 379): the money per tonne-km, the crew and animals' food and water carried as
cargo mass, a crew that follows from what the hull needs to sail and to hold off boarders, and
robbery that falls as the crew grows.

Pure functions only (no game is built), unittest-style like test_transport.py.
"""

QUICK_TOPIC = True

import unittest

from sim.engine import foreign_routes
from sim.geography import freight_cost, provisions, sea_freight, transport

# Stated prices in one unit of money: grain per kg, the hourly wage, the market rate.
GRAIN_PRICE_PER_KG = 0.3
WAGE_PER_HOUR = 0.12
MARKET_RATE = 0.08

CART = transport.draught_freight_physical_inputs(transport.OX, 2, transport.CART, transport.DIRT_TRACK)
PACK = transport.pack_freight_physical_inputs(transport.MULE, 10)
HULL = sea_freight.sailing_freight_physical_inputs()
CART_PRICES = freight_cost.CarrierPrices(vehicle=200.0, animals=3000.0)
PACK_PRICES = freight_cost.CarrierPrices(vehicle=200.0, animals=8000.0)
HULL_PRICES = freight_cost.CarrierPrices(vehicle=HULL.cargo_tonnes * 800.0 * 0.05)


def rate(inputs, prices, working_days, loss=0.0):
    return freight_cost.freight_money_per_tonne_km(
        inputs, GRAIN_PRICE_PER_KG, WAGE_PER_HOUR, prices, MARKET_RATE, working_days, 1.0, loss)


def grain_reach_km(inputs, prices, working_days, loss=0.0):
    """Distance at which hauling a tonne of grain costs as much as the grain, counting the carried
    provisions: where the haul eats the value."""
    per_tonne_km = rate(inputs, prices, working_days, loss)
    low, high = 1.0, 1.0e6
    for _ in range(80):
        middle = 0.5 * (low + high)
        cost = freight_cost.leg_money_per_tonne(per_tonne_km, inputs, middle)
        low, high = (middle, high) if cost < GRAIN_PRICE_PER_KG * 1000.0 else (low, middle)
    return low


class GrainReachTests(unittest.TestCase):

    def test_grain_hauled_by_land_costs_its_value_within_a_few_hundred_km(self):
        # The freight function alone (no carried mass): this holds before provisions are counted.
        for inputs, prices in ((CART, CART_PRICES), (PACK, PACK_PRICES)):
            per_tonne_km = rate(inputs, prices, freight_cost.LAND_WORKING_DAYS_PER_YEAR)
            self.assertLess(GRAIN_PRICE_PER_KG * 1000.0 / per_tonne_km, 400.0)

    def test_a_ship_moves_grain_much_further_at_a_lower_cost_per_kg(self):
        land = rate(CART, CART_PRICES, freight_cost.LAND_WORKING_DAYS_PER_YEAR)
        sea = rate(HULL, HULL_PRICES, sea_freight.SAILING_DAYS_PER_YEAR)
        self.assertLess(sea, land / 10.0)
        land_reach = grain_reach_km(CART, CART_PRICES, freight_cost.LAND_WORKING_DAYS_PER_YEAR)
        sea_reach = grain_reach_km(HULL, HULL_PRICES, sea_freight.SAILING_DAYS_PER_YEAR,
                                   sea_freight.hull_loss_per_thousand_km())
        self.assertGreater(sea_reach, 10.0 * land_reach)

    def test_carried_provisions_shorten_the_land_reach(self):
        carried_free = rate(CART, CART_PRICES, freight_cost.LAND_WORKING_DAYS_PER_YEAR)
        reach_without = GRAIN_PRICE_PER_KG * 1000.0 / carried_free
        reach_with = grain_reach_km(CART, CART_PRICES, freight_cost.LAND_WORKING_DAYS_PER_YEAR)
        self.assertLess(reach_with, reach_without)


class ProvisionsTests(unittest.TestCase):

    def test_the_share_delivered_falls_with_distance_to_nothing_for_a_cart(self):
        shares = [provisions.delivered_share(CART, km) for km in (0.0, 100.0, 400.0)]
        self.assertEqual(shares[0], 1.0)
        self.assertGreater(shares[0], shares[1])
        self.assertGreater(shares[1], shares[2])
        self.assertEqual(provisions.delivered_share(CART, 1.0e6), 0.0)

    def test_a_pack_string_carries_less_of_its_load_per_day_than_a_hull_per_km(self):
        self.assertLess(provisions.delivered_share(PACK, 300.0), provisions.delivered_share(HULL, 300.0))

    def test_water_counts_as_mass_beside_food(self):
        people = 5.0
        carried = provisions.person_provisions_kg_per_day(people)
        self.assertGreater(carried, people * provisions.PERSON_GRAIN_RATION_KG_PER_DAY)

    def test_the_hull_carries_its_crew_water_as_well_as_their_food(self):
        self.assertGreater(HULL.carried_kg_per_day, HULL.feed_kg_per_day)

    def test_an_unreachable_leg_costs_infinity(self):
        self.assertEqual(freight_cost.leg_money_per_tonne(1.0, CART, 1.0e6), float("inf"))


class HullCrewTests(unittest.TestCase):

    def test_no_hull_is_sailed_by_one_person(self):
        self.assertGreaterEqual(sea_freight.crew_to_sail(1.0), 2)

    def test_a_bigger_hull_needs_more_hands_but_fewer_per_tonne(self):
        small, large = sea_freight.crew_to_sail(40.0), sea_freight.crew_to_sail(400.0)
        self.assertGreater(large, small)
        self.assertLess(large / 400.0, small / 40.0)

    def test_the_default_hull_is_crewed_from_its_rig(self):
        crew = sea_freight.crew_to_sail(sea_freight.MERCHANT_HULL_CARGO_TONNES)
        self.assertEqual(HULL.carried_kg_per_day, provisions.person_provisions_kg_per_day(crew))
        self.assertAlmostEqual(HULL.feed_kg_per_day, crew * provisions.PERSON_GRAIN_RATION_KG_PER_DAY)


class RobberyTests(unittest.TestCase):

    def test_a_larger_crew_is_taken_less_often(self):
        losses = [sea_freight.boarding_loss_share(crew) for crew in (1, 4, 12, 80)]
        self.assertEqual(losses, sorted(losses, reverse=True))
        self.assertGreater(losses[0], 0.9)
        self.assertLess(losses[-1], 0.1)

    def test_hull_losses_per_distance_fall_with_the_crew(self):
        self.assertGreater(sea_freight.hull_loss_per_thousand_km(2),
                           sea_freight.hull_loss_per_thousand_km(20))

    def test_a_crew_cannot_take_losses_below_the_weather_alone(self):
        self.assertGreater(sea_freight.hull_loss_per_thousand_km(1.0e6), 0.0)


class LegPricingTests(unittest.TestCase):

    def test_restocking_keeps_an_overlong_leg_finite(self):
        self.assertLess(freight_cost.leg_money_per_tonne(
            1.0, CART, 1.0e6, restock_days=provisions.RESTOCK_INTERVAL_DAYS), float("inf"))

    def test_provisions_raise_a_leg_above_its_rate_times_distance(self):
        self.assertGreater(freight_cost.leg_money_per_tonne(1.0, CART, 200.0), 200.0)


class _StubEconomy(foreign_routes.ForeignRoutesMixin):
    def _carrier_models(self):
        return {"cart": (CART, CART_PRICES, 250.0, 0.0), "sail": (HULL, HULL_PRICES, 150.0, 0.0)}

    def _freight_handling_costs(self):
        return {"sail": 5.0}


class RoutePricingTests(unittest.TestCase):

    def test_a_route_leg_costs_more_per_tonne_for_the_carried_provisions(self):
        legs = (foreign_routes.Leg("a", "b", "cart", 200.0, 200.0, 11.0),
                foreign_routes.Leg("b", "c", "sail", 1000.0, 20.0, 9.0))
        priced = _StubEconomy()._with_carried_provisions(foreign_routes.Route(legs))
        self.assertGreater(priced.legs[0].cost_per_tonne, 200.0)
        self.assertGreater(priced.legs[1].cost_per_tonne, 20.0)
        self.assertGreater(priced.legs[0].cost_per_tonne / 200.0, priced.legs[1].cost_per_tonne / 20.0)

    def test_the_handling_fee_is_not_scaled(self):
        legs = (foreign_routes.Leg("b", "c", "sail", 1000.0, 5.0, 9.0),)
        priced = _StubEconomy()._with_carried_provisions(foreign_routes.Route(legs))
        self.assertEqual(priced.legs[0].cost_per_tonne, 5.0)

    def test_a_mode_without_a_model_is_left_as_found(self):
        legs = (foreign_routes.Leg("a", "b", "teleport", 10.0, 7.0, 1.0),)
        self.assertEqual(_StubEconomy()._with_carried_provisions(foreign_routes.Route(legs)).legs, legs)


if __name__ == "__main__":
    unittest.main()
