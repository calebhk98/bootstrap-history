"""The array a kernel reads in place of area_of(good, tile) and a key lookup, and the memory arrays built from the tables."""
QUICK_TOPIC = True

import unittest


from sim.economy.market_memory import KEY_SEPARATOR
from sim.economy.year_arrays import YearArrays
from sim.economy.year_arrays_memory import NO_AREA, market_cells, markets_by_good_tile
from sim.tests.year_close_fixture import GOODS, TILES, economy_of


class MarketsByGoodTileTests(unittest.TestCase):
    def test_each_cell_is_the_row_of_the_goods_market_the_area_map_names(self):
        setup, record, view, _ledger, area_map = economy_of(2)
        arrays = YearArrays.build(setup, record, area_map, view)
        record.memory.tables.admit_goods_markets(good + KEY_SEPARATOR + area_map.area_of(good, tile) for good in GOODS for tile in TILES)
        grid = markets_by_good_tile(record.memory, arrays.matrices.goods, arrays.area_index)
        names = record.memory.tables.goods_markets.names
        for good in GOODS:
            for tile in TILES:
                row = grid[arrays.matrices.goods.row[good], arrays.tiles.row[tile]]
                self.assertEqual(names[row], good + KEY_SEPARATOR + area_map.area_of(good, tile))

    def test_a_market_the_memory_has_not_numbered_is_minus_one(self):
        setup, record, view, _ledger, area_map = economy_of(2)
        arrays = YearArrays.build(setup, record, area_map, view)
        record.memory.tables.load_state(None)
        grid = markets_by_good_tile(record.memory, arrays.matrices.goods, arrays.area_index)
        self.assertTrue((grid == -1).all())

    def test_a_market_numbered_later_is_found_by_the_next_read(self):
        setup, record, view, _ledger, area_map = economy_of(2)
        arrays = YearArrays.build(setup, record, area_map, view)
        record.memory.tables.load_state(None)
        before = markets_by_good_tile(record.memory, arrays.matrices.goods, arrays.area_index).copy()
        good, tile = GOODS[0], TILES[0]
        record.memory.prices[good + KEY_SEPARATOR + area_map.area_of(good, tile)] = 1.0
        after = markets_by_good_tile(record.memory, arrays.matrices.goods, arrays.area_index)
        cell = (arrays.matrices.goods.row[good], arrays.tiles.row[tile])
        self.assertEqual((before[cell], after[cell] >= 0), (-1, True))

    def test_market_cells_leave_out_markets_of_goods_the_arrays_do_not_hold(self):
        setup, record, view, _ledger, area_map = economy_of(2)
        arrays = YearArrays.build(setup, record, area_map, view)
        record.memory.prices["unlisted_good|nowhere"] = 1.0
        good_rows, area_columns = market_cells(record.memory, arrays.matrices.goods, arrays.area_index)
        row = record.memory.tables.goods_markets.number("unlisted_good|nowhere")
        self.assertEqual((good_rows[row], area_columns[row]), (NO_AREA, NO_AREA))


if __name__ == "__main__":
    unittest.main()
