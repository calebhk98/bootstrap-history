"""Complaint 563: a located material is priced at the buyer as its making cost at the site plus freight from the
nearest of its places, as a tracked mineral is."""

import unittest

from sim.geography import api as geography_api
from sim.tests.harness import sim

GOOD = "pozzolana_kg"


class LocatedMaterialFreightTests(unittest.TestCase):
    """Scenario (Complaint 640 audit): the engine places a located material and prices its carriage from a game."""

    @classmethod
    def setUpClass(cls):
        cls.norse = sim(civ="norse_900ad", capital=1.0)
        cls.rome = sim(capital=1.0)

    def test_located_goods_are_placed_by_their_entry(self):
        s = self.norse
        entry = geography_api.load_geography()["located_materials"]["pozzolana"]
        self.assertIn(GOOD, entry["goods"])
        self.assertTrue(s.geography.source_tiles(GOOD))

    def test_pozzolana_freight_follows_the_route_to_the_nearest_site(self):
        s = self.norse
        distance_km = s.material_freight_distance_km(GOOD)
        self.assertIsNotNone(distance_km)
        self.assertGreater(distance_km, 0.0)
        per_kg = s.material_freight_cost_per_kg(GOOD)
        self.assertGreater(per_kg, 0.0)
        self.assertAlmostEqual(per_kg, s.domestic_haul_money_per_tonne(GOOD) / 1000.0, places=9)

    def test_buyer_pays_site_cost_plus_carriage(self):
        s = self.norse
        site_cost = s._material_price_per_kg(GOOD)
        carriage_per_tonne = s.material_carriage_per_tonne(GOOD, site_cost * 1000.0)
        self.assertGreaterEqual(carriage_per_tonne, s.material_freight_cost_per_kg(GOOD) * 1000.0)
        self.assertGreater(carriage_per_tonne, 0.0)

    def test_holder_of_a_site_pays_no_freight(self):
        s = self.rome
        self.assertEqual(s.material_freight_distance_km(GOOD), 0.0)
        self.assertEqual(s.material_carriage_per_tonne(GOOD, 100.0), 0.0)

    def test_the_multiplier_stand_in_is_gone(self):
        entry = geography_api.load_geography()["located_materials"]["pozzolana"]
        self.assertEqual(entry["cost_multiplier"], 1)
        s = self.norse
        self.assertEqual(s.geography.material_cost_factor("mat_pozzolana"), 1.0)


if __name__ == "__main__":
    unittest.main()
