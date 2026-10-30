"""The land module's views of carriage over the map (sim/land/map_carriage.py): the modes that carry a cargo, the facts of the modes,
the crews, and the cheapest and fastest ways between tiles. Each is called on a land module over a small map of two bordering
tiles written out here; no game."""
QUICK_TOPIC = True

import unittest

from sim.geography import api as geography
from sim.tests import land_host

SMALL_MAP = geography.map_of_tiles({
    "a": {"lat": 12.5, "lon": 3.25, "land_area_km2": 200.0, "coastal": True, "borders": ["b"]},
    "b": {"lat": 13.5, "lon": 3.25, "land_area_km2": 100.5, "coastal": False, "borders": ["a"]}})


def small_land():
    module = land_host.build({"id": "rome", "home_tiles": ["a", "b"]})
    module._map_cache = SMALL_MAP
    return module


class ModesTests(unittest.TestCase):
    def test_parties_that_hold_nothing_can_only_walk(self):
        self.assertEqual(small_land().modes_usable([[]]), ["foot"])

    def test_the_modes_that_take_goods_include_the_cart_and_not_the_drove(self):
        modes = small_land().modes_carrying("goods")
        self.assertIn("cart", modes)
        self.assertNotIn("drove", modes)
        self.assertEqual(modes, sorted(modes))


class CarriageFactsTests(unittest.TestCase):
    def test_the_drove_is_the_mode_whose_cargo_walks_and_loses_some_each_day(self):
        facts = small_land().carriage_facts()
        self.assertEqual(facts["walking_modes"], ["drove"])
        self.assertEqual(facts["loss_per_day"], {"drove": 0.001})

    def test_a_river_boat_pays_dues_by_the_tonne_and_a_foot_traveller_none(self):
        dues = small_land().carriage_facts()["dues_hours_per_tonne"]
        self.assertEqual((dues["river_boat"], dues["foot"]), (1.0, 0.0))


class ModeCarrierTests(unittest.TestCase):
    def test_rail_is_a_train_and_not_a_drove(self):
        carrier = small_land().mode_carrier("rail")
        self.assertIn("fuel_material", carrier["train"])
        self.assertIsNone(carrier["droving"])

    def test_the_drove_is_a_droving_carrier_and_not_a_train(self):
        carrier = small_land().mode_carrier("drove")
        self.assertIn("inputs", carrier["droving"])
        self.assertIsNone(carrier["train"])

    def test_the_cart_is_neither(self):
        self.assertEqual(small_land().mode_carrier("cart"), {"train": None, "droving": None})


class ModeCrewsTests(unittest.TestCase):
    def test_a_mode_that_names_a_crew_is_given_its_crew_trade_and_hours(self):
        crews = small_land().mode_crews(["cart"])
        self.assertEqual(set(crews), {"cart"})
        self.assertIn("crew_trade", crews["cart"])
        self.assertGreater(crews["cart"]["crew_hours_per_tonne_km"], 0.0)


class RoutesTests(unittest.TestCase):
    def test_the_cheapest_route_between_bordering_tiles_is_one_leg_on_foot(self):
        found = small_land().cheapest_route(["a"], ["b"], ["foot"])
        self.assertEqual([(leg["from"], leg["to"], leg["mode"]) for leg in found["legs"]], [("a", "b", "foot")])
        self.assertAlmostEqual(found["km"], 144.5534, places=3)

    def test_no_mode_joins_nothing(self):
        self.assertIsNone(small_land().cheapest_route(["a"], ["b"], []))

    def test_the_fastest_route_is_asked_for_by_keyword(self):
        found = small_land().cheapest_route(["a"], ["b"], ["foot"], fastest=True)
        self.assertAlmostEqual(found["days"], 6.6874, places=3)

    def test_the_days_to_each_reachable_tile_are_counted_from_the_origins(self):
        reached = small_land().reach_days(["a"], ["foot"], 100.0)
        self.assertEqual(reached["a"], 0.0)
        self.assertAlmostEqual(reached["b"], 6.6874, places=3)

    def test_a_budget_shorter_than_the_walk_reaches_only_the_origin(self):
        self.assertEqual(small_land().reach_days(["a"], ["foot"], 1.0), {"a": 0.0})


if __name__ == "__main__":
    unittest.main()
