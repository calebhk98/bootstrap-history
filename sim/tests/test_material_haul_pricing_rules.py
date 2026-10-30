"""Complaint 563, 568: a material's carriage, freight markup and distance read the haul route the one
haul function priced; an unlocated material or one made on held ground costs nothing to carry. Each test calls one
method on a stand-in whose route is written out. The leg pricing itself is test_material_haul_legs and
test_freight_domestic_haul; the markup arithmetic is test_material_freight."""
QUICK_TOPIC = True

import types
import unittest

from sim.markets.goods_market import GoodsMarket
from sim.freight.module import Freight
from sim.tests import module_harness

CART_ROUTE = types.SimpleNamespace(legs=("leg",), cost_per_tonne=200.0)
HELD_ROUTE = types.SimpleNamespace(legs=(), cost_per_tonne=0.0)


class _Hauled(Freight):
    """The freight module with the route search and the cargo's own cost written out."""
    route, cargo_share = CART_ROUTE, 0.1

    def material_haul_route(self, material):
        return self.route

    def domestic_cargo_cost_share(self, material, route):
        return self.cargo_share


def freight(route, tiles=("mine_01",), distance=120.0, book_price=0.5):
    module = module_harness.build(_Hauled, views={
        "material_source_tiles": lambda material: tiles, "route_km_to": lambda sources: distance,
        "material_price": lambda material: book_price})
    module.route = route
    return module


class Distance(unittest.TestCase):
    def test_the_distance_is_the_geographys_route_to_the_nearest_source_tile(self):
        self.assertEqual(freight(CART_ROUTE).material_distance_km("coal"), 120.0)

    def test_a_material_geography_places_nowhere_has_no_distance(self):
        self.assertIsNone(freight(CART_ROUTE, tiles=()).material_distance_km("gold"))


class Factor(unittest.TestCase):
    def test_a_haul_with_a_cost_marks_the_price_up_by_the_freight_over_the_price_plus_the_cargo_share(self):
        self.assertAlmostEqual(freight(CART_ROUTE).material_freight_factor("coal"), 1.0 + 0.2 / 0.5 + 0.1)

    def test_a_dearer_haul_marks_up_more(self):
        far = types.SimpleNamespace(legs=("leg",), cost_per_tonne=400.0)
        self.assertGreater(freight(far).material_freight_factor("coal"), freight(CART_ROUTE).material_freight_factor("coal"))

    def test_no_route_no_legs_or_no_price_leaves_the_price_alone(self):
        self.assertEqual(freight(None).material_freight_factor("gold"), 1.0)
        self.assertEqual(freight(HELD_ROUTE).material_freight_factor("coal"), 1.0)
        self.assertEqual(freight(CART_ROUTE, book_price=None).material_freight_factor("coal"), 1.0)


class Carriage(unittest.TestCase):
    def test_carriage_is_the_routes_cost_plus_the_cargo_share_of_the_price(self):
        self.assertAlmostEqual(freight(CART_ROUTE).material_carriage_per_tonne("coal", 1000.0), 200.0 + 0.1 * 1000.0)

    def test_a_material_on_held_ground_or_unplaced_costs_nothing_to_carry(self):
        self.assertEqual(freight(HELD_ROUTE).material_carriage_per_tonne("coal", 100.0), 0.0)
        self.assertEqual(freight(None).material_carriage_per_tonne("gold", 100.0), 0.0)


class HaulRoute(unittest.TestCase):
    def test_no_source_tile_means_no_route(self):
        module = module_harness.build(Freight, views={"material_source_tiles": lambda material: ()})
        self.assertIsNone(module.material_haul_route("gold"))


class QuoteVolume(unittest.TestCase):
    def quote(self, brought, offered, market):
        sim = types.SimpleNamespace(
            _material_tag=lambda material: (material, None),
            economy=types.SimpleNamespace(agent_offered_tonnes=lambda material: offered),
            _material_market_tonnes=lambda key: market)
        stand_in = types.SimpleNamespace(
            _sim=sim, acting_party_id="founder", price_at_tile_per_tonne=lambda material: 10.0,
            import_tonnes_available=lambda material: brought, _carriage_per_tonne=lambda material, price: 1.0,
            purchase_cost=lambda material, tonnes: (0.0, 11.0), sale_proceeds=lambda *args: (0.0, 9.0),
            sold_tonnes=lambda key, party: 0.0, price_kind=lambda material: "market",
            making_cost_per_tonne=lambda material: None)
        return GoodsMarket.quote(stand_in, "alum_kg")["market_available_tonnes_per_year"]

    def test_the_volume_is_the_economys_offer_else_the_throttles_market_tonnes(self):
        self.assertEqual(self.quote(None, None, 5.0), 5.0)
        self.assertEqual(self.quote(None, 3.0, 5.0), 3.0)

    def test_a_partners_good_quotes_what_the_partner_brings(self):
        self.assertEqual(self.quote(2.0, 3.0, 5.0), 2.0)

    def test_a_material_with_no_price_has_no_quote(self):
        stand_in = types.SimpleNamespace(_sim=None, price_at_tile_per_tonne=lambda material: None)
        self.assertIsNone(GoodsMarket.quote(stand_in, "ghost"))


if __name__ == "__main__":
    unittest.main()
