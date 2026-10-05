"""Market areas: tiles that share a price for a good because carriage between them costs little against its value.

Synthetic grid for the rules; real tiles of two civilisations for scale. Resolving a civilisation's
tiles through `region_to_tiles` is test scaffolding only."""
import json
import unittest

from sim.economy import market_areas, tile_costs
from sim.economy.types import GoodSpec
from sim.tests.test_economy_tile_costs import GEOGRAPHY_PATH, REAL_HANDLING, REAL_RATES, civ_tile_ids, grid, grid_table

GRAIN = GoodSpec("grain_kg", 1.0, 0.1, 0.0, "food")
SILVER = GoodSpec("silver_kg", 1.0, 0.0, 0.0, "metal")
SILK = GoodSpec("silk_kg", 1.0, 0.01, 0.0, "textile")
# Prices per kg in denarii, plausible for the book period (test inputs).
GRAIN_PRICE, SILVER_PRICE, SILK_PRICE = 0.05, 1000.0, 300.0


def population(tile_ids):
    return {tile_id: 1000.0 - index for index, tile_id in enumerate(sorted(tile_ids))}


class PartitionTests(unittest.TestCase):
    def setUp(self):
        self.tiles = grid(5, 5)
        self.table = grid_table(self.tiles, {"cart": 1.0})
        self.step = self.table.cost_per_tonne("t_0_0", "t_1_0")

    def test_dear_goods_form_one_area_and_cheap_goods_one_per_tile(self):
        pops = population(self.tiles)
        one = market_areas.partition(self.tiles, self.table, 1e9, pops, 0.15, "silver")
        self.assertEqual(len(one), 1)
        self.assertEqual(len(one[0].tiles), 25)
        each = market_areas.partition(self.tiles, self.table, 0.5 * self.step / 0.15, pops, 0.15, "grain")
        self.assertEqual(len(each), 25)

    def test_every_tile_is_in_exactly_one_area_within_the_threshold(self):
        value = 4.5 * self.step / 0.2
        areas = market_areas.partition(self.tiles, self.table, value, population(self.tiles), 0.2, "x")
        seen = [tile for area in areas for tile in area.tiles]
        self.assertEqual(sorted(seen), sorted(self.tiles))
        for area in areas:
            for tile in area.tiles:
                self.assertLessEqual(self.table.cost_per_tonne(tile, area.anchor_tile), 0.2 * value + 1e-9)
        self.assertTrue(1 < len(areas) < 25)

    def test_most_populous_tile_is_the_first_anchor_and_ties_break_by_id(self):
        pops = {tile_id: 10.0 for tile_id in self.tiles}
        pops["t_3_3"] = 99.0
        areas = market_areas.partition(self.tiles, self.table, 2.5 * self.step / 0.15, pops, 0.15, "x")
        self.assertIn("t_3_3", {area.anchor_tile for area in areas})
        again = market_areas.partition(self.tiles, self.table, 2.5 * self.step / 0.15, pops, 0.15, "x")
        self.assertEqual(areas, again)

    def test_disconnected_tiles_never_share_an_area(self):
        pieces = {tile_id: tile for tile_id, tile in self.tiles.items() if tile_id.startswith(("t_0_", "t_4_"))}
        table = grid_table(pieces, {"cart": 1.0})
        areas = market_areas.partition(pieces, table, 1e12, population(pieces), 0.5, "x")
        self.assertEqual(len(areas), 2)

    def test_free_value_gives_one_area_per_tile(self):
        areas = market_areas.partition(self.tiles, self.table, 0.0, population(self.tiles), 0.15, "waste")
        self.assertEqual(len(areas), 25)


class AreaMapTests(unittest.TestCase):
    def setUp(self):
        self.tiles = grid(5, 5)
        rates = {"cart": 1.0}
        self.table = grid_table(self.tiles, rates)
        step = self.table.cost_per_tonne("t_0_0", "t_1_0")
        self.grain_price = 0.5 * step / 0.15 / 1000.0
        self.silver_price = 1e6 * self.grain_price
        self.pops = population(self.tiles)
        self.goods = [(GRAIN, self.grain_price), (SILVER, self.silver_price)]

    def build(self, goods=None):
        return market_areas.AreaMap(self.tiles, self.table, goods or self.goods, self.pops)

    def test_silver_is_one_area_and_grain_is_per_tile(self):
        area_map = self.build()
        self.assertEqual(len(area_map.areas("silver_kg")), 1)
        self.assertEqual(len(area_map.areas("grain_kg")), 25)
        self.assertEqual(area_map.goods(), ("grain_kg", "silver_kg"))

    def test_area_of_and_areas_agree_and_carry_the_good(self):
        area_map = self.build()
        for area in area_map.areas("silver_kg"):
            self.assertEqual(area.good_id, "silver_kg")
            for tile in area.tiles:
                self.assertEqual(area_map.area_of("silver_kg", tile), area.area_id)
        self.assertEqual(area_map.market_area_of("grain_kg", "t_2_2").tiles, ("t_2_2",))

    def test_goods_of_similar_value_share_one_partition(self):
        twin = GoodSpec("barley_kg", 1.0, 0.1, 0.0, "food")
        area_map = self.build(self.goods + [(twin, self.grain_price * 1.05)])
        self.assertEqual(area_map.bucket_count(), 2)
        self.assertEqual(area_map.area_of("barley_kg", "t_1_1"), area_map.area_of("grain_kg", "t_1_1"))

    def test_value_per_tonne_uses_unit_mass(self):
        sack = GoodSpec("sack", 50.0, 0.0, 0.0, "food")
        self.assertAlmostEqual(market_areas.value_per_tonne(sack, 10.0), 200.0)

    def test_area_ids_are_stable_across_rebuilds(self):
        first, second = self.build(), self.build(list(reversed(self.goods)))
        for good in first.goods():
            self.assertEqual(first.areas(good), second.areas(good))

    def test_small_price_move_keeps_ids_and_unknown_names_raise(self):
        area_map = self.build()
        nudged = self.build([(GRAIN, self.grain_price * 1.01), (SILVER, self.silver_price)])
        self.assertEqual(area_map.area_of("grain_kg", "t_1_1"), nudged.area_of("grain_kg", "t_1_1"))
        with self.assertRaises(KeyError):
            area_map.area_of("unknown", "t_1_1")
        with self.assertRaises(KeyError):
            area_map.area_of("grain_kg", "nowhere")


class RealTilesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GEOGRAPHY_PATH, encoding="utf-8") as handle:
            cls.geography = json.load(handle)

    def area_counts(self, civ_name):
        tile_ids = civ_tile_ids(self.geography, civ_name)
        tiles = tile_costs.tiles_from_geography(self.geography, tile_ids)
        table = tile_costs.carriage_table(tiles, REAL_RATES, REAL_HANDLING)
        pops = {tile_id: tile.land_area_km2 * tile.arable_fraction * tile.fertility for tile_id, tile in tiles.items()}
        goods = [(GRAIN, GRAIN_PRICE), (SILK, SILK_PRICE), (SILVER, SILVER_PRICE)]
        area_map = market_areas.AreaMap(tiles, table, goods, pops)
        connected = max(len(table.costs_from(tile_id)) for tile_id in tiles)
        return len(tiles), connected, {good: len(area_map.areas(good)) for good in area_map.goods()}

    def check(self, civ_name):
        tile_count, connected, counts = self.area_counts(civ_name)
        print("%s: %d tiles, largest connected %d, areas %s" % (civ_name, tile_count, connected, counts))
        self.assertLessEqual(counts["silver_kg"], max(1, tile_count // 10))
        self.assertGreaterEqual(counts["grain_kg"], tile_count // 3)
        self.assertLess(counts["silver_kg"], counts["silk_kg"] + 1)
        self.assertLess(counts["silk_kg"], counts["grain_kg"])

    def test_rome(self):
        self.check("rome_100ad")

    def test_han_china(self):
        self.check("han_china_100ad")


if __name__ == "__main__":
    unittest.main()
