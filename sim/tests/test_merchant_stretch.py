"""Complaints/517: a merchant knows prices only in its stretch (the areas a year's haul reaches from its home and from the tiles it
traded at), so a good crosses a long route through a chain of merchants, each working the stretch it knows; the stretch grows by
trading and fades when a tile goes unvisited."""

QUICK_TOPIC = True

import unittest

from sim.economy import merchants, merchants_stretch
from sim.economy.merchants import Merchant
from sim.economy.types import MarketArea
from sim.tests.test_economy_merchants import SPECS, View

TILES = ("t0", "t1", "t2", "t3", "t4")
DAYS_PER_STEP = 200.0         # one step is inside a year's haul; two steps are not


class LineCarriage:
    """Tiles on a line, a tonne costing a little a step."""
    scale = 1.0

    def costs_from(self, source):
        return {tile: 0.01 * abs(TILES.index(tile) - TILES.index(source)) for tile in TILES}

    def days_between(self, from_tile, to_tile):
        return abs(TILES.index(from_tile) - TILES.index(to_tile)) * DAYS_PER_STEP


class LineMap:
    def __init__(self):
        self._areas = tuple(MarketArea("area_%s" % tile, "salt", (tile,), tile) for tile in TILES)

    def goods(self):
        return ["salt"]

    def areas(self, good):
        return self._areas

    def area_of(self, good, tile):
        return "area_%s" % tile


PRICES = {("salt", "area_%s" % tile): price for tile, price in zip(TILES, (2.0, 4.0, 6.0, 8.0, 10.0))}


def hops(home, traded=()):
    """The (source tile, destination tile) pairs the merchant at `home` finds worth hauling."""
    who = Merchant("m_" + home, home, "owner", 100.0, dict(PRICES), {})
    who.traded_tiles = {tile: 0 for tile in traded}
    rows = merchants.candidate_routes(who, View(PRICES), LineCarriage(), LineMap(), {}, SPECS, 0.0)
    return {(row[2].anchor_tile, row[3].anchor_tile) for row in rows}


class StretchTests(unittest.TestCase):
    def test_the_known_flags_cover_the_areas_a_years_haul_reaches_from_the_stretch(self):
        areas = LineMap().areas("salt")
        self.assertEqual(merchants_stretch.known_flags("salt", areas, LineCarriage(), {"t0"}), [True, True, False, False, False])
        self.assertEqual(merchants_stretch.known_flags("salt", areas, LineCarriage(), {"t0", "t4"}), [True, True, False, True, True])

    def test_a_merchant_does_not_see_an_area_outside_its_stretch(self):
        seen = {tile for pair in hops("t0") for tile in pair}
        self.assertTrue(seen)
        self.assertTrue(seen <= {"t0", "t1"})

    def test_a_good_crosses_the_line_through_a_chain_of_merchants(self):
        west, middle, east = hops("t0"), hops("t2"), hops("t4")
        self.assertNotIn(("t0", "t4"), west | middle | east)
        self.assertIn(("t0", "t1"), west)
        self.assertIn(("t1", "t3"), middle)
        self.assertIn(("t3", "t4"), east)

    def test_trading_at_a_tile_brings_its_neighbours_into_the_stretch(self):
        self.assertIn(("t0", "t4"), hops("t0", traded=("t3",)))

    def test_a_tile_fades_from_the_stretch_when_left_unvisited(self):
        kept = {"t3": 0}
        for _year in range(3):
            kept = merchants_stretch.after_year(kept, [], 3)
        self.assertEqual(kept, {"t3": 3})
        self.assertEqual(merchants_stretch.after_year(kept, [], 3), {})

    def test_a_tile_traded_at_again_is_fresh(self):
        self.assertEqual(merchants_stretch.after_year({"t3": 2, "t1": 1}, ["t3", "t4"], 3), {"t1": 2, "t3": 0, "t4": 0})

    def test_the_stretch_always_holds_home(self):
        self.assertEqual(merchants_stretch.stretch_of("t0", ["t3"]), frozenset({"t0", "t3"}))
        self.assertEqual(merchants_stretch.stretch_of("t0", []), frozenset({"t0"}))

    def test_routes_name_their_source_and_destination_tiles(self):
        routes = {("salt", "t0"): (("t1", "area_t1", 1.0), ("t2", "area_t2", 2.0)), ("fish", "t3"): (("t4", "area_t4", 1.0),)}
        self.assertEqual(merchants_stretch.routes_tiles(routes), ["t0", "t1", "t2", "t3", "t4"])


if __name__ == "__main__":
    unittest.main()
