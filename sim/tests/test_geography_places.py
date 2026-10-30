"""The distance between two places of the map: tiles and regions by id, nothing for an id the map does not have."""

QUICK_TOPIC = True

import unittest

from sim.geography.api import haversine_km, load_geography
from sim.geography.places import distance_between_places


class PlaceDistanceTests(unittest.TestCase):
    def test_two_tiles_are_the_great_circle_between_their_coordinates(self):
        tiles = load_geography()["land_tiles"]["tiles"]
        first_id, second_id = sorted(tiles)[0], sorted(tiles)[-1]
        first, second = tiles[first_id], tiles[second_id]
        self.assertAlmostEqual(distance_between_places(first_id, second_id),
                               haversine_km(first["lat"], first["lon"], second["lat"], second["lon"]))

    def test_a_place_the_map_does_not_have_is_no_distance(self):
        tile_id = sorted(load_geography()["land_tiles"]["tiles"])[0]
        self.assertEqual(distance_between_places(tile_id, "no_such_place"), 0.0)


if __name__ == "__main__":
    unittest.main()
