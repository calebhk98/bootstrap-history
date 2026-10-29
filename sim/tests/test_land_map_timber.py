"""The land module's views of the forest on the map (sim/land/map_timber.py): the wood a tile grows, the wood standing once some is
felled, and the felled ledger after cuts and a year's regrowth. Called on a land module over the base map; no game."""
QUICK_TOPIC = True

import unittest

from sim.geography import api as geography
from sim.geography import forest_timber
from sim.tests import land_host

WORLD_MAP = geography.open_map()
FOREST_TILE = max(geography.tile_ids(WORLD_MAP), key=lambda tile: forest_timber.full_tonnes(WORLD_MAP, tile))
BARE_TILE = next(tile for tile in geography.tile_ids(WORLD_MAP) if forest_timber.full_tonnes(WORLD_MAP, tile) == 0.0)
FULL = forest_timber.full_tonnes(WORLD_MAP, FOREST_TILE)


def land():
    return land_host.build({"id": "rome", "home_tiles": [FOREST_TILE]})


class ForestIncrementTests(unittest.TestCase):
    def test_a_forest_tile_grows_wood_and_a_bare_tile_none(self):
        self.assertAlmostEqual(land().forest_increment([FOREST_TILE]), 8.6121, places=3)
        self.assertEqual(land().forest_increment([BARE_TILE]), 0.0)

    def test_no_tiles_grow_none(self):
        self.assertEqual(land().forest_increment([]), 0.0)


class FelledLedgerTests(unittest.TestCase):
    def test_each_cut_comes_off_its_tile_in_turn(self):
        felled = land().felled_after_cuts({}, [(FOREST_TILE, FULL / 8.0), (FOREST_TILE, FULL / 8.0)])
        self.assertAlmostEqual(felled[FOREST_TILE], FULL / 4.0)

    def test_the_ledger_given_is_not_changed(self):
        before = {FOREST_TILE: 1.0}
        land().felled_after_cuts(before, [(FOREST_TILE, 5.0)])
        self.assertEqual(before, {FOREST_TILE: 1.0})

    def test_no_cuts_leave_the_ledger_as_it_was(self):
        self.assertEqual(land().felled_after_cuts({FOREST_TILE: 3.0}, []), {FOREST_TILE: 3.0})

    def test_a_year_of_regrowth_lowers_what_is_felled(self):
        felled = {FOREST_TILE: FULL / 4.0}
        self.assertLess(land().felled_after_regrowth(felled)[FOREST_TILE], FULL / 4.0)


class TimberOnTileTests(unittest.TestCase):
    def test_a_felled_tile_stands_at_what_is_left_and_has_a_haul_to_it(self):
        found = land().timber_on_tile({FOREST_TILE: FULL / 4.0}, FOREST_TILE)
        self.assertAlmostEqual(found["standing_tonnes"], FULL * 0.75)
        self.assertGreater(found["haul_km"], 0.0)

    def test_a_tile_with_nothing_standing_has_no_haul(self):
        self.assertEqual(land().timber_on_tile({}, BARE_TILE), {"standing_tonnes": 0.0, "haul_km": None})

    def test_a_tile_cut_to_nothing_has_no_haul(self):
        self.assertIsNone(land().timber_on_tile({FOREST_TILE: FULL * 2.0}, FOREST_TILE)["haul_km"])


if __name__ == "__main__":
    unittest.main()
