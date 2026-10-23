"""Carriage between tiles: the economy prices hauls over geography's route graph, not a graph of its own.

Synthetic tile grids (laid on a geography map of just those tiles) for the rules; the base map is read in
test_economy_tile_costs_geography."""
QUICK_TOPIC = True
import math
import os
import unittest

from sim.economy import tile_costs
from sim.economy.types import TileSpec
from sim.geography import api as geography_api

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Plausible money per tonne-km in denarii and port handling per tonne (test inputs, not model data).
REAL_RATES = {"cart": 0.19, "pack": 0.5, "river_boat": 0.05, "sail": 0.007}
REAL_HANDLING = {"sail": 0.2}
CROPPED_SHARE = 2.0 / 3.0   # a test input: the share of open fields cropped in a year


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


if __name__ == "__main__":
    unittest.main()
