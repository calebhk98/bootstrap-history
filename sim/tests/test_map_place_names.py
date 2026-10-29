"""Complaint 637: a map overlay's `places` catalogue names the places on a tile; the tile fields every screen shows
(`map`, `move`) carry them."""
QUICK_TOPIC = True

import types
import unittest

from sim.geography import tile_names
from sim.ui.proto.screen_map import tile_place


def map_with_places(places):
    return types.SimpleNamespace(catalogue=lambda name: {entry["id"]: entry for entry in places} if name == "places" else {})


PLACES = [{"id": "a", "name": "Small", "tile": "here_01", "rank": 1},
          {"id": "b", "name": "Great", "tile": "here_01", "rank": 9},
          {"id": "c", "name": "Elsewhere", "tile": "nowhere_01"}]


class PlaceNameTests(unittest.TestCase):

    def test_places_on_a_tile_come_highest_rank_first(self):
        self.assertEqual(tile_names.places_on(map_with_places(PLACES), "here_01"), ["Great", "Small"])

    def test_equal_ranks_come_in_name_order(self):
        places = [{"id": "x", "name": "Zed", "tile": "t"}, {"id": "y", "name": "Abe", "tile": "t"}]
        self.assertEqual(tile_names.places_on(map_with_places(places), "t"), ["Abe", "Zed"])

    def test_a_tile_with_no_place_has_none(self):
        self.assertEqual(tile_names.places_on(map_with_places(PLACES), "empty_01"), [])

    def test_a_tile_row_carries_the_places_the_map_names(self):
        self.assertEqual(tile_place("here_01", ["Great", "Small"])["places"], ["Great", "Small"])

    def test_a_tile_with_no_place_changes_no_row(self):
        self.assertNotIn("places", tile_place("here_01", []))
        self.assertNotIn("places", tile_place("here_01"))


if __name__ == "__main__":
    unittest.main()
