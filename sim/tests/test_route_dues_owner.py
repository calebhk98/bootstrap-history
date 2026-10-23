"""Complaint 599: a route's dues belong to the holder of the tile where they are levied, are charged per tonne
carried. The settlement into a treasury is test_route_dues_settlement."""

import unittest

QUICK_TOPIC = True

from sim.geography import api as geography_api


def _legs(*stops):
    """Legs [(origin tile, mode)] as the route search states them."""
    return [{"from": tile, "mode": mode} for tile, mode in stops]


class DuesByHolder(unittest.TestCase):

    def test_each_due_goes_to_the_holder_of_the_tile_it_is_levied_at(self):
        owners = {"a": "rome", "b": "carthage"}
        levied = geography_api.route_dues_levied(
            _legs(("a", "river_boat"), ("b", "sail")), {"river_boat": 2.0, "sail": 3.0}, owners.get)
        self.assertEqual([(due["tile"], due["holder"], due["per_tonne"]) for due in levied],
                         [("a", "rome", 2.0), ("b", "carthage", 3.0)])

    def test_dues_scale_with_the_tonnes_carried(self):
        owners = {"a": "rome"}
        once = geography_api.route_dues_by_holder(_legs(("a", "sail")), {"sail": 3.0}, owners.get, tonnes=10.0)
        twice = geography_api.route_dues_by_holder(_legs(("a", "sail")), {"sail": 3.0}, owners.get, tonnes=20.0)
        self.assertAlmostEqual(twice["rome"], 2.0 * once["rome"])

    def test_dues_are_levied_once_where_the_haul_changes_to_a_mode_not_on_each_hop(self):
        owners = {"a": "rome", "b": "carthage", "c": "rome"}
        levied = geography_api.route_dues_levied(
            _legs(("a", "sail"), ("b", "sail"), ("c", "foot"), ("a", "sail")), {"sail": 3.0}, owners.get)
        self.assertEqual([(due["tile"], due["holder"]) for due in levied], [("a", "rome"), ("a", "rome")])

    def test_a_mode_with_no_dues_and_an_unheld_tile_levy_nothing(self):
        self.assertEqual(geography_api.route_dues_levied(
            _legs(("a", "foot"), ("zz", "sail")), {"sail": 3.0}, {"a": "rome"}.get), [])


if __name__ == "__main__":
    unittest.main()
