"""A newcomer is not sited on a tile whose ground is all granted: runs there would get no land."""
QUICK_TOPIC = True

import unittest

from sim.economy.location_land import land_short_tiles, headroom_with_land


class HeadroomWithLandTest(unittest.TestCase):
    def test_a_recipe_on_land_has_no_room_on_a_short_tile(self):
        self.assertEqual(headroom_with_land(50.0, takes_land=True, tile_is_land_short=True), 0.0)

    def test_a_recipe_without_land_keeps_its_room(self):
        self.assertEqual(headroom_with_land(50.0, takes_land=False, tile_is_land_short=True), 50.0)

    def test_a_tile_with_land_keeps_its_room(self):
        self.assertEqual(headroom_with_land(50.0, takes_land=True, tile_is_land_short=False), 50.0)


class LandShortTilesTest(unittest.TestCase):
    def test_a_tile_where_a_landed_producer_was_cut_is_short(self):
        rows = [("a", 0.0, True), ("b", -1.0, True), ("c", 5.0, True)]     # (tile, land_run_cap, recipe takes land)
        self.assertEqual(land_short_tiles(rows), {"a", "c"})

    def test_a_cap_on_a_recipe_that_takes_no_land_does_not_count(self):
        self.assertEqual(land_short_tiles([("a", 0.0, False)]), set())


if __name__ == "__main__":
    unittest.main()
