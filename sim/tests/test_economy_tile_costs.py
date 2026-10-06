"""Carriage between tiles: the economy prices hauls over geography's route graph, not a graph of its own.

Synthetic tile grids (laid on a geography map of just those tiles) for the rules; the base map for
scale, timing and the proof that links geography knows (rivers, sea lanes) reach the economy.
Picking a civilisation's tiles through `region_to_tiles` is test scaffolding only: civilisations will
hold tile ids directly."""
import json
import math
import os
import time
import unittest

from sim.economy import tile_costs
from sim.economy.types import TileSpec
from sim.geography import api as geography_api

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Plausible money per tonne-km in denarii and port handling per tonne (test inputs, not model data).
REAL_RATES = {"cart": 0.19, "pack": 0.5, "river_boat": 0.05, "sail": 0.007}
REAL_HANDLING = {"sail": 0.2}


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


def grid_table(tiles, rates, handling=None):
    """A carriage table over a geography map of just these tiles."""
    return tile_costs.carriage_table(tiles, rates, handling, world_map=tile_costs.world_map_of(tiles))


def unit_cost_table(tiles, from_tile, to_tile):
    """A table over these tiles whose cart rate is set so a tonne from `from_tile` to `to_tile` costs exactly one."""
    world_map = tile_costs.world_map_of(tiles)
    rate = 1.0 / tile_costs.carriage_table(tiles, {"cart": 1.0}, world_map=world_map).cost_per_tonne(from_tile, to_tile)
    for _attempt in range(8):
        table = tile_costs.carriage_table(tiles, {"cart": rate}, world_map=world_map)
        cost = table.cost_per_tonne(from_tile, to_tile)
        if cost == 1.0:
            break
        rate = rate * 1.0 / cost if cost != 0.0 else rate
        rate = math.nextafter(rate, math.inf if cost < 1.0 else 0.0)
    return table


def star_tiles(centre, leaves, radius_km, centre_latitude=40.0, centre_longitude=10.0):
    """A centre tile bordering each leaf tile, every leaf the same great-circle distance from it (at evenly spread bearings)."""
    angle = radius_km / 6371.0
    latitude, longitude = math.radians(centre_latitude), math.radians(centre_longitude)
    tiles = {centre: TileSpec(centre, centre_latitude, centre_longitude, 1000.0, False, tuple(leaves), 0.3, 1.0)}
    for index, leaf in enumerate(leaves):
        bearing = 2.0 * math.pi * index / len(leaves)
        leaf_latitude = math.asin(math.sin(latitude) * math.cos(angle)
                                  + math.cos(latitude) * math.sin(angle) * math.cos(bearing))
        leaf_longitude = longitude + math.atan2(math.sin(bearing) * math.sin(angle) * math.cos(latitude),
                                                math.cos(angle) - math.sin(latitude) * math.sin(leaf_latitude))
        tiles[leaf] = TileSpec(leaf, math.degrees(leaf_latitude), math.degrees(leaf_longitude), 1000.0, False,
                               (centre,), 0.3, 1.0)
    return tiles


def civ_tile_ids(geography, civ_name):
    """TEST SCAFFOLDING: the civ's tiles through its home regions' tile lists."""
    with open(os.path.join(ROOT, "data", "civilizations", civ_name + ".json"), encoding="utf-8") as handle:
        civ = json.load(handle)
    mapping = geography["land_tiles"]["region_to_tiles"]
    return sorted({tile for region in civ["home_regions"] for tile in mapping.get(region, [])})


class GridTests(unittest.TestCase):
    def test_overland_cost_is_the_route_cost_and_adds_along_a_chain(self):
        tiles = grid(4, 1)
        table = grid_table(tiles, {"cart": 2.0})
        step = table.cost_per_tonne("t_0_0", "t_1_0")
        found = geography_api.route(["t_0_0"], ["t_1_0"], ["cart"], mode_costs={"cart": 2.0},
                                    handling_costs={}, world_map=tile_costs.world_map_of(tiles))
        self.assertAlmostEqual(step, found["cost_per_tonne"])
        self.assertGreater(step, 0.0)
        self.assertAlmostEqual(table.cost_per_tonne("t_0_0", "t_3_0"), 3.0 * step, places=6)
        self.assertEqual(table.cost_per_tonne("t_2_0", "t_2_0"), 0.0)
        self.assertAlmostEqual(table.cost_per_tonne("t_3_0", "t_0_0"), 3.0 * step, places=6)

    def test_cheapest_land_mode_is_used(self):
        tiles = grid(2, 1)
        both = grid_table(tiles, {"cart": 2.0, "pack": 0.5})
        pack_only = grid_table(tiles, {"pack": 0.5})
        self.assertAlmostEqual(both.cost_per_tonne("t_0_0", "t_1_0"), pack_only.cost_per_tonne("t_0_0", "t_1_0"))

    def test_disconnected_tiles_cost_infinity(self):
        tiles = grid(3, 1)
        isolated = {tile_id: TileSpec(tile_id, tile.latitude, tile.longitude, 1.0, False, (), 0.3, 1.0)
                    for tile_id, tile in tiles.items()}
        table = grid_table(isolated, {"cart": 1.0})
        self.assertEqual(table.cost_per_tonne("t_0_0", "t_2_0"), math.inf)

    def test_sea_beats_land_over_a_long_coast_when_the_sea_rate_is_low(self):
        tiles = grid(1, 6, coastal_columns=(0,))
        with_sea = grid_table(tiles, {"cart": 1.0, "sail": 0.1})
        without_sea = grid_table(tiles, {"cart": 1.0})
        self.assertLess(with_sea.cost_per_tonne("t_0_0", "t_0_5"), 0.5 * without_sea.cost_per_tonne("t_0_0", "t_0_5"))

    def test_sea_links_need_both_ends_coastal(self):
        coastal = grid_table(grid(2, 1, coastal_columns=(0, 1)), {"sail": 1.0})
        inland = grid_table(grid(2, 1), {"sail": 1.0})
        self.assertLess(coastal.cost_per_tonne("t_0_0", "t_1_0"), math.inf)
        self.assertEqual(inland.cost_per_tonne("t_0_0", "t_1_0"), math.inf)

    def test_handling_is_charged_when_a_haul_takes_to_the_sea(self):
        tiles = grid(1, 2, coastal_columns=(0,))
        plain = grid_table(tiles, {"sail": 1.0})
        handled = grid_table(tiles, {"sail": 1.0}, {"sail": 7.0})
        self.assertAlmostEqual(handled.cost_per_tonne("t_0_0", "t_0_1") - plain.cost_per_tonne("t_0_0", "t_0_1"), 7.0)

    def test_a_river_on_the_map_carries_a_haul_the_roads_would_not(self):
        tiles = grid(3, 1)
        records = {tile_id: {"lat": tile.latitude, "lon": tile.longitude, "coastal": False,
                             "borders": list(tile.borders)} for tile_id, tile in tiles.items()}
        river_map = geography_api.map_of_tiles(records)
        river_map.layers["river_id"] = {"id": "river_id", "values": {tile_id: "the_river" for tile_id in tiles}}
        dry = tile_costs.carriage_table(tiles, {"cart": 5.0, "river_boat": 0.1}, world_map=tile_costs.world_map_of(tiles))
        wet = tile_costs.carriage_table(tiles, {"cart": 5.0, "river_boat": 0.1}, world_map=river_map)
        self.assertLess(wet.cost_per_tonne("t_0_0", "t_2_0"), 0.5 * dry.cost_per_tonne("t_0_0", "t_2_0"))


class GeographyIsTheSourceTests(unittest.TestCase):
    """The economy's carriage costs are geography's route costs on the same tiles (Complaint 408)."""

    @classmethod
    def setUpClass(cls):
        cls.geography = geography_api.load_geography()
        cls.tile_ids = civ_tile_ids(cls.geography, "rome_100ad")
        cls.tiles = tile_costs.tiles_from_geography(cls.geography, cls.tile_ids)

    def test_a_river_link_geography_knows_is_cheaper_by_boat_in_the_economy(self):
        inside = set(self.tile_ids)
        rivers = [(a, b) for a, b, _mode, _km in geography_api.freight_links(["river_boat"])
                  if a in inside and b in inside]
        self.assertTrue(rivers, "the civilisation's tiles hold a navigable river link")
        downstream = [(source, target) for a, b in rivers for source, target in ((a, b), (b, a))
                      if geography_api.route([source], [target], ["river_boat"]) is not None]
        self.assertTrue(downstream, "a boat can run along one of them")
        first, second = downstream[0]
        with_boats = tile_costs.carriage_table(self.tiles, {"cart": 5.0, "river_boat": 0.01})
        without = tile_costs.carriage_table(self.tiles, {"cart": 5.0})
        self.assertLess(with_boats.cost_per_tonne(first, second), without.cost_per_tonne(first, second))

    def test_costs_equal_geographys_route_cost_for_the_same_rates(self):
        table = tile_costs.carriage_table(self.tiles, REAL_RATES, REAL_HANDLING)
        first, last = self.tile_ids[0], self.tile_ids[-1]
        found = geography_api.route([first], [last], sorted(REAL_RATES), mode_costs=REAL_RATES,
                                    handling_costs=REAL_HANDLING)
        self.assertIsNotNone(found)
        self.assertAlmostEqual(table.cost_per_tonne(first, last), found["cost_per_tonne"], places=6)

    def test_no_tile_of_the_civilisation_is_cut_off(self):
        table = tile_costs.carriage_table(self.tiles, REAL_RATES, REAL_HANDLING)
        reached = table.costs_from(self.tile_ids[0])
        self.assertEqual(set(reached), set(self.tile_ids))

    def test_all_pairs_for_the_largest_civilisation_is_fast_and_cached(self):
        names = ("rome_100ad", "han_china_100ad", "england_1300", "mexica_1500", "norse_900ad")
        biggest = max((civ_tile_ids(self.geography, name) for name in names), key=len)
        tiles = tile_costs.tiles_from_geography(self.geography, biggest)
        self.assertGreater(len(tiles), 30)
        geography_api.route([biggest[0]], [biggest[-1]], ["cart"])      # builds the map's graph once
        started = time.perf_counter()
        table = tile_costs.carriage_table(tiles, REAL_RATES, REAL_HANDLING)
        table.warm()
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 5.0, "all-pairs took %.3f s for %d tiles" % (elapsed, len(tiles)))
        started = time.perf_counter()
        table.warm()
        self.assertLess(time.perf_counter() - started, 0.01)
        first, last = biggest[0], biggest[-1]
        self.assertAlmostEqual(table.cost_per_tonne(first, last), table.cost_per_tonne(last, first), delta=1e-6 * table.cost_per_tonne(first, last))

    def test_tiles_from_geography_reads_fields(self):
        tile_id = sorted(self.geography["land_tiles"]["tiles"])[0]
        tiles = tile_costs.tiles_from_geography(self.geography, [tile_id])
        record = self.geography["land_tiles"]["tiles"][tile_id]
        self.assertEqual(tiles[tile_id].latitude, record["lat"])
        self.assertEqual(tiles[tile_id].fertility, record["fertility_quality_multiplier"])
        self.assertEqual(tiles[tile_id].borders, tuple(record["borders"]))


if __name__ == "__main__":
    unittest.main()
