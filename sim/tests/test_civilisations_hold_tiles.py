"""Complaints/136: a civilisation holds tiles; a region is an optional label naming a starting claim.

The held tiles feed settlement, the frontier and road lengths and the economy's tiles; a civilisation
that lists `home_tiles` is held by those tiles whatever its region labels say.
"""
import json
import os
import unittest

from sim.geography import api, territory

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _civilisation(civilisation_id):
    with open(os.path.join(_ROOT, "data", "civilizations", civilisation_id + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


class TilesHeldTests(unittest.TestCase):

    def test_region_labels_name_the_starting_tiles(self):
        civ = _civilisation("rome_100ad")
        self.assertEqual(api.tiles_held(civ), api.tiles_of_regions(civ["home_regions"]))

    def test_listed_tiles_win_over_the_labels(self):
        civ = dict(_civilisation("rome_100ad"))
        two = api.tiles_of_regions(["italia"])[:2]
        civ["home_tiles"] = two
        self.assertEqual(api.tiles_held(civ), sorted(two))

    def test_a_civilisation_with_neither_holds_nothing(self):
        self.assertEqual(api.tiles_held({}), [])
        self.assertEqual(api.tiles_held({"home_regions": ["not_a_region"]}), [])

    def test_listed_tiles_unknown_to_the_map_are_not_held(self):
        civ = {"home_tiles": [api.tile_ids()[0], "nowhere_00"]}
        self.assertEqual(api.tiles_held(civ), [api.tile_ids()[0]])

    def test_frontier_and_roads_follow_the_tiles_held(self):
        tiles = api.tiles_of_regions(["italia"])
        one = territory.holdings(tiles[:1])
        self.assertEqual(one.tile_count, 1)
        self.assertEqual(one.road_km, 0.0)
        self.assertGreater(territory.holdings(tiles).road_km, 0.0)

    def test_settlement_follows_the_tiles_held(self):
        tiles = api.tiles_of_regions(["italia"])
        shares = sum(api.settlement.population_share(tiles, tile) for tile in api.settlement.tile_ids(tiles))
        self.assertAlmostEqual(shares, 1.0, places=9)


if __name__ == "__main__":
    unittest.main()
