"""The wage rule over a block of trades and labour areas (sim/economy/wage_block.py and its kernels): each kernel on written-out
rows, and the block, the kept table and `wage_grid` against `trade_wages.wage_in_area` / `wage_in_view` cell by cell, bit for bit."""

QUICK_TOPIC = True

import unittest

import numpy as np

from sim.economy import trade_wages
from sim.economy.market_memory import market_key
from sim.economy.setup import labour_area
from sim.economy.wage_block import WageRuleTable, wage_rule_block
from sim.economy.wage_block_kernels import labour_market_matrix, market_rows_of, wage_in_row, wage_rule_grid
from sim.economy.year_arrays import wage_grid, wage_grid_by_cells
from sim.economy.year_arrays_recipes import Names
from sim.tests.year_close_fixture import TILES, TRADES, economy_of

NAN = np.nan


class Kernels(unittest.TestCase):
    def test_the_matrix_holds_each_markets_row_at_its_trade_and_area(self):
        matrix = labour_market_matrix(np.array([0, 1, 1]), np.array([2, 0, 2]), 3, 2, 3)
        self.assertEqual(matrix.tolist(), [[-1, -1, 0], [1, -1, 2]])

    def test_rows_ask_by_number_and_a_number_of_minus_one_is_no_market(self):
        matrix = np.array([[-1, -1, 0], [1, -1, 2]])
        rows = market_rows_of(matrix, np.array([1, -1, 0]), np.array([2, 0, -1]))
        self.assertEqual(rows.tolist(), [[2, 1, -1], [-1, -1, -1], [0, -1, -1]])

    def test_a_market_row_of_minus_one_or_a_market_with_no_wage_is_nan(self):
        wages = np.array([2.0, NAN])
        self.assertEqual((wage_in_row(wages, 0), np.isnan(wage_in_row(wages, 1)), np.isnan(wage_in_row(wages, -1))), (2.0, True, True))

    def test_the_rule_takes_what_was_paid_first(self):
        grid = wage_rule_grid(np.array([[0]]), np.array([3.0]), np.array([-1]), np.array([True]), np.array([9.0]), np.array([0.5]), 2.0, 1.0)
        self.assertEqual(grid.tolist(), [[3.0]])

    def test_a_trade_held_nowhere_is_priced_at_its_opening_wage_times_the_level(self):
        grid = wage_rule_grid(np.array([[-1]]), np.array([3.0]), np.array([-1]), np.array([False]), np.array([9.0]), np.array([0.5]), 2.0, 1.0)
        self.assertEqual(grid.tolist(), [[18.0]])

    def test_a_trade_held_elsewhere_is_priced_on_the_areas_unskilled_wage_plus_its_premium(self):
        grid = wage_rule_grid(np.array([[-1, -1]]), np.array([4.0]), np.array([0, -1]), np.array([True]), np.array([9.0]), np.array([0.5]), 2.0, 1.5)
        self.assertEqual(grid.tolist(), [[6.0, 2.25]])

    def test_nothing_to_price_from_is_nan_not_zero(self):
        grid = wage_rule_grid(np.array([[-1]]), np.array([4.0]), np.array([-1]), np.array([True]), np.array([NAN]), np.array([0.0]), 2.0, NAN)
        self.assertTrue(np.isnan(grid[0, 0]))


def areas_of(tiles):
    return [labour_area(tile) for tile in tiles]


class BlockAgainstTheRule(unittest.TestCase):
    def test_every_trade_and_area_has_the_wage_in_area_gives(self):
        for seed in range(8):
            setup, record, _view, _ledger, _area_map = economy_of(seed)
            areas = areas_of(TILES) + ["labour:nowhere"]
            block = wage_rule_block(setup, record.memory, TRADES, areas)
            for row, trade in enumerate(TRADES):
                for column, area in enumerate(areas):
                    self.assertEqual(block[row, column], trade_wages.wage_in_area(setup, record.memory, trade, area))

    def test_a_memory_that_holds_no_wage_prices_every_trade_on_the_opening_wages(self):
        setup, record, _view, _ledger, _area_map = economy_of(1)
        record.memory.wages.clear()
        block = wage_rule_block(setup, record.memory, TRADES, areas_of(TILES))
        for row, trade in enumerate(TRADES):
            for column, area in enumerate(areas_of(TILES)):
                self.assertEqual(block[row, column], trade_wages.wage_in_area(setup, record.memory, trade, area))

    def test_a_trade_the_setup_does_not_know_is_a_key_error(self):
        setup, record, _view, _ledger, _area_map = economy_of(1)
        with self.assertRaises(KeyError):
            wage_rule_block(setup, record.memory, ("glassblower",), areas_of(TILES))

    def test_with_no_opening_wage_for_the_unskilled_trade_the_rule_refuses_as_it_did(self):
        setup, record, _view, _ledger, _area_map = economy_of(1)
        record.memory.wages.clear()
        del setup.opening_wages["labourer"]
        with self.assertRaises(KeyError):
            wage_rule_block(setup, record.memory, TRADES, areas_of(TILES))


class TableAndGrid(unittest.TestCase):
    def test_wage_in_view_gives_the_rules_wage_for_every_cell(self):
        for seed in range(6):
            setup, record, view, _ledger, _area_map = economy_of(seed)
            for trade in TRADES:
                for area in areas_of(TILES) + ["labour:nowhere"]:
                    self.assertEqual(trade_wages.wage_in_view(setup, view, trade, area), trade_wages.wage_in_area(setup, record.memory, trade, area))

    def test_the_table_follows_a_wage_written_to_the_memory(self):
        setup, record, view, _ledger, _area_map = economy_of(2)
        area = labour_area(TILES[0])
        record.memory.wages[market_key("smith", area)] = 41.0
        self.assertEqual(trade_wages.wage_in_view(setup, view, "smith", area), 41.0)
        record.memory.wages.pop(market_key("smith", area))
        self.assertEqual(trade_wages.wage_in_view(setup, view, "smith", area), trade_wages.wage_in_area(setup, record.memory, "smith", area))

    def test_the_table_is_filled_again_only_after_a_write(self):
        setup, record, _view, _ledger, _area_map = economy_of(2)
        table = WageRuleTable(setup, record.memory, lambda: areas_of(TILES))
        table.wage("smith", labour_area(TILES[0]))
        table.wage("miller", labour_area(TILES[1]))
        self.assertEqual(table.refreshes, 1)
        record.memory.wages[market_key("smith", labour_area(TILES[0]))] = 5.0
        table.wage("smith", labour_area(TILES[0]))
        self.assertEqual(table.refreshes, 2)

    def test_a_cell_the_table_does_not_hold_is_none(self):
        setup, record, _view, _ledger, _area_map = economy_of(2)
        table = WageRuleTable(setup, record.memory, lambda: areas_of(TILES))
        self.assertEqual((table.wage("glassblower", labour_area(TILES[0])), table.wage("smith", "labour:nowhere")), (None, None))

    def test_the_wage_grid_is_the_cell_by_cell_grid(self):
        for seed in range(6):
            setup, record, view, _ledger, _area_map = economy_of(seed)
            trades, tiles = Names.of(TRADES), Names.of(TILES)
            np.testing.assert_array_equal(wage_grid(setup, view, trades, tiles), wage_grid_by_cells(setup, view, trades, tiles))


if __name__ == "__main__":
    unittest.main()
