"""Carriage between tiles: the neighbour graph, land and sea links, cheapest paths, and the freight rates.

Synthetic tile grids for the rules; the real geography for scale and timing. Picking a civilisation's
tiles through `region_to_tiles` is test scaffolding only: civilisations will hold tile ids directly."""
import json
import math
import os
import time
import unittest

from sim.economy import tile_costs
from sim.economy.types import TileSpec
from sim.world.freight_cost import CarrierPrices

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEOGRAPHY_PATH = os.path.join(ROOT, "data", "world", "geography.json")

# Plausible book prices in denarii (test inputs, not model data).
WAGE_PER_HOUR = 0.1
FEED_PRICE_PER_KG = 0.03
ANNUAL_RATE = 0.06
CARRIER_PRICES = {
    tile_costs.DRAUGHT_MODE: CarrierPrices(vehicle=150.0, animals=240.0),
    tile_costs.PACK_MODE: CarrierPrices(vehicle=40.0, animals=600.0),
    tile_costs.SEA_MODE: CarrierPrices(vehicle=20000.0),
}


def grid(columns, rows, coastal_columns=(), spacing_degrees=3.5):
    """A rectangular grid of tiles, four-neighbour borders; tiles in `coastal_columns` are coastal."""
    tiles = {}
    for column in range(columns):
        for row in range(rows):
            tile_id = "t_%d_%d" % (column, row)
            borders = []
            for d_column, d_row in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= column + d_column < columns and 0 <= row + d_row < rows:
                    borders.append("t_%d_%d" % (column + d_column, row + d_row))
            tiles[tile_id] = TileSpec(tile_id, 40.0 + row * spacing_degrees, 10.0 + column * spacing_degrees,
                                      150000.0, column in coastal_columns, tuple(borders), 0.3, 1.0)
    return tiles


def real_rates():
    return tile_costs.money_per_tonne_km_by_mode(CARRIER_PRICES, WAGE_PER_HOUR, FEED_PRICE_PER_KG, ANNUAL_RATE)


def civ_tile_ids(geography, civ_name):
    """TEST SCAFFOLDING: the civ's tiles through its home regions' tile lists."""
    with open(os.path.join(ROOT, "data", "civilizations", civ_name + ".json"), encoding="utf-8") as handle:
        civ = json.load(handle)
    mapping = geography["land_tiles"]["region_to_tiles"]
    return sorted({tile for region in civ["home_regions"] for tile in mapping.get(region, [])})


class GeometryTests(unittest.TestCase):
    def test_great_circle_known_distance(self):
        # One degree of latitude is a sixtieth-ish of a quarter circle: about 111 km.
        self.assertAlmostEqual(tile_costs.great_circle_km(0, 0, 1, 0), 111.2, delta=0.5)
        self.assertEqual(tile_costs.great_circle_km(10, 20, 10, 20), 0.0)

    def test_neighbours_are_symmetric_and_limited_to_the_set(self):
        tiles = grid(2, 1)
        half = {"t_0_0": TileSpec("t_0_0", 40, 10, 1.0, False, ("t_1_0", "outside"), 0.3, 1.0),
                "t_1_0": TileSpec("t_1_0", 40, 13.5, 1.0, False, (), 0.3, 1.0)}
        graph = tile_costs.neighbour_graph(half)
        self.assertEqual(graph["t_1_0"], ("t_0_0",))
        self.assertEqual(graph["t_0_0"], ("t_1_0",))
        self.assertEqual(set(tile_costs.neighbour_graph(tiles)), {"t_0_0", "t_1_0"})

    def test_tiles_from_geography_reads_fields(self):
        with open(GEOGRAPHY_PATH, encoding="utf-8") as handle:
            geography = json.load(handle)
        tile_id = sorted(geography["land_tiles"]["tiles"])[0]
        tiles = tile_costs.tiles_from_geography(geography, [tile_id])
        record = geography["land_tiles"]["tiles"][tile_id]
        self.assertEqual(tiles[tile_id].latitude, record["lat"])
        self.assertEqual(tiles[tile_id].fertility, record["fertility_quality_multiplier"])
        self.assertEqual(tiles[tile_id].borders, tuple(record["borders"]))


class CarriageTableTests(unittest.TestCase):
    def test_overland_cost_is_distance_times_rate_and_adds_along_a_chain(self):
        tiles = grid(4, 1)
        table = tile_costs.carriage_table(tiles, {tile_costs.DRAUGHT_MODE: 2.0})
        step = table.cost_per_tonne("t_0_0", "t_1_0")
        self.assertAlmostEqual(
            step, 2.0 * tile_costs.LAND_ROUTE_DETOUR_FACTOR
            * tile_costs.tile_distance_km(tiles["t_0_0"], tiles["t_1_0"]))
        self.assertAlmostEqual(table.cost_per_tonne("t_0_0", "t_3_0"), 3.0 * step, places=6)
        self.assertEqual(table.cost_per_tonne("t_2_0", "t_2_0"), 0.0)
        self.assertAlmostEqual(table.cost_per_tonne("t_3_0", "t_0_0"), 3.0 * step, places=6)

    def test_cheapest_land_mode_is_used(self):
        tiles = grid(2, 1)
        both = tile_costs.carriage_table(tiles, {tile_costs.DRAUGHT_MODE: 2.0, tile_costs.PACK_MODE: 1.0})
        pack_only = tile_costs.carriage_table(tiles, {tile_costs.PACK_MODE: 1.0})
        self.assertAlmostEqual(both.cost_per_tonne("t_0_0", "t_1_0"), pack_only.cost_per_tonne("t_0_0", "t_1_0"))

    def test_disconnected_tiles_cost_infinity(self):
        tiles = grid(3, 1)
        isolated = dict(tiles)
        isolated["t_1_0"] = TileSpec("t_1_0", 40, 13.5, 1.0, False, (), 0.3, 1.0)
        isolated["t_0_0"] = TileSpec("t_0_0", 40, 10.0, 1.0, False, (), 0.3, 1.0)
        isolated["t_2_0"] = TileSpec("t_2_0", 40, 17.0, 1.0, False, (), 0.3, 1.0)
        table = tile_costs.carriage_table(isolated, {tile_costs.DRAUGHT_MODE: 1.0})
        self.assertEqual(table.cost_per_tonne("t_0_0", "t_2_0"), math.inf)

    def test_sea_beats_land_over_a_long_coast_when_the_sea_rate_is_low(self):
        tiles = grid(1, 6, coastal_columns=(0,))
        rates = {tile_costs.DRAUGHT_MODE: 1.0, tile_costs.SEA_MODE: 0.1}
        with_sea = tile_costs.carriage_table(tiles, rates)
        without_sea = tile_costs.carriage_table(tiles, {tile_costs.DRAUGHT_MODE: 1.0})
        self.assertLess(with_sea.cost_per_tonne("t_0_0", "t_0_5"), 0.5 * without_sea.cost_per_tonne("t_0_0", "t_0_5"))

    def test_sea_links_need_both_ends_coastal_and_range(self):
        tiles = grid(4, 1, coastal_columns=(0, 3), spacing_degrees=3.5)
        far = tile_costs.tile_distance_km(tiles["t_0_0"], tiles["t_3_0"])
        edges = tile_costs.build_edges(tiles)
        sea = [edge for edge in edges if edge.modes == (tile_costs.SEA_MODE,)]
        self.assertEqual(bool(sea), far <= tile_costs.SEA_LINK_RANGE_KM)
        inland = tile_costs.build_edges(grid(4, 1))
        self.assertFalse([edge for edge in inland if tile_costs.SEA_MODE in edge.modes])

    def test_extra_link_is_a_hook_for_rivers(self):
        tiles = grid(1, 1)
        wider = grid(3, 1)
        link = tile_costs.Link("t_0_0", "t_2_0", tile_costs.RIVER_MODE, 100.0)
        edges = tile_costs.build_edges(wider, [link])
        table = tile_costs.carriage_table(wider, {tile_costs.DRAUGHT_MODE: 5.0, tile_costs.RIVER_MODE: 0.1}, edges=edges)
        self.assertAlmostEqual(table.cost_per_tonne("t_0_0", "t_2_0"), 10.0)
        self.assertEqual(len(tiles), 1)

    def test_handling_is_charged_per_sea_leg(self):
        tiles = grid(1, 2, coastal_columns=(0,))
        rates = {tile_costs.SEA_MODE: 1.0}
        plain = tile_costs.carriage_table(tiles, rates)
        handled = tile_costs.carriage_table(tiles, rates, {tile_costs.SEA_MODE: 7.0})
        self.assertAlmostEqual(handled.cost_per_tonne("t_0_0", "t_0_1") - plain.cost_per_tonne("t_0_0", "t_0_1"), 7.0)


class FreightRateTests(unittest.TestCase):
    def test_rates_are_positive_and_sea_is_cheapest_per_tonne_km(self):
        rates = real_rates()
        self.assertEqual(set(rates), {"draught", "pack", "sea"})
        self.assertTrue(all(rate > 0.0 for rate in rates.values()))
        self.assertLess(rates["sea"], rates["draught"])
        self.assertLess(rates["draught"], rates["pack"])

    def test_rates_follow_prices(self):
        base = real_rates()
        dearer = tile_costs.money_per_tonne_km_by_mode(CARRIER_PRICES, 2 * WAGE_PER_HOUR, FEED_PRICE_PER_KG, ANNUAL_RATE)
        self.assertTrue(all(dearer[mode] > base[mode] for mode in base))

    def test_only_named_modes_are_priced(self):
        self.assertEqual(set(tile_costs.money_per_tonne_km_by_mode(
            {"draught": CARRIER_PRICES["draught"]}, WAGE_PER_HOUR, FEED_PRICE_PER_KG, ANNUAL_RATE)), {"draught"})


class RealGeographyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GEOGRAPHY_PATH, encoding="utf-8") as handle:
            cls.geography = json.load(handle)

    def test_all_pairs_for_the_largest_civilisation_is_fast_and_cached(self):
        names = ("rome_100ad", "han_china_100ad", "england_1300", "mexica_1500", "norse_900ad")
        biggest = max((civ_tile_ids(self.geography, name) for name in names), key=len)
        tiles = tile_costs.tiles_from_geography(self.geography, biggest)
        self.assertGreater(len(tiles), 30)
        rates, handling = real_rates(), tile_costs.handling_money_per_tonne_by_mode(WAGE_PER_HOUR)
        started = time.perf_counter()
        table = tile_costs.carriage_table(tiles, rates, handling)
        table.warm()
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 1.0, "all-pairs took %.3f s for %d tiles" % (elapsed, len(tiles)))
        started = time.perf_counter()
        table.warm()
        self.assertLess(time.perf_counter() - started, 0.01)
        first, last = biggest[0], biggest[-1]
        self.assertAlmostEqual(table.cost_per_tonne(first, last), table.cost_per_tonne(last, first), places=6)


if __name__ == "__main__":
    unittest.main()
