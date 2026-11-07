"""The year arrays (numba port item 0b) hold what the records hold, and stay in step as producers are replaced, enter and
leave. Each test builds the arrays from a random small economy (year_close_fixture) and reads them back against the
records and against the market memory's own methods; no game."""

QUICK_TOPIC = True

import math
import unittest
from dataclasses import replace

import numpy as np

from sim.economy import trade_wages
from sim.economy.market_memory import KEY_SEPARATOR
from sim.economy.setup import labour_area
from sim.economy.types import QUOTE_BEST_UNFILLED_BID, QUOTE_LOWEST_UNFILLED_ASK
from sim.economy.year_arrays import YearArrays
from sim.economy.year_arrays_memory import NO_AREA
from sim.tests.year_close_fixture import AREAS, GOODS, TILES, economy_of


def nan_or(value):
    return math.nan if value is None else value


class ProducerColumnsHoldTheRecords(unittest.TestCase):
    def test_every_column_is_the_records_field(self):
        for seed in range(6):
            setup, record, view, _ledger, area_map = economy_of(seed)
            arrays = YearArrays.build(setup, record, area_map, view)
            columns = arrays.producers
            self.assertEqual(columns.ids, tuple(sorted(record.producers)))
            for row, producer_id in enumerate(columns.ids):
                producer = record.producers[producer_id]
                self.assertEqual(arrays.matrices.recipes.ids[columns.recipe_row[row]], producer.recipe_id)
                self.assertEqual(arrays.tiles.ids[columns.tile_row[row]], producer.tile)
                for name in ("capacity_runs", "yield_factor", "cash_target", "expected_sales", "last_runs", "land_rent_per_run",
                             "workshops", "idle_years", "years_of_loss"):
                    self.assertEqual(getattr(columns, name)[row], getattr(producer, name))
                np.testing.assert_equal(columns.land_run_cap[row], nan_or(producer.land_run_cap))
                np.testing.assert_equal(columns.staffed_runs[row], nan_or(producer.staffed_runs))
                count = columns.history_count[row]
                self.assertEqual(tuple(columns.earnings_history[row, :count]), producer.net_earnings_history)
                self.assertEqual(tuple(columns.revenue_history[row, :len(producer.revenue_history)]), producer.revenue_history)
                for slot, column in enumerate(arrays.matrices.slot_goods[columns.recipe_row[row]]):
                    if column >= 0:
                        np.testing.assert_equal(columns.expected_prices[row, slot],
                                                nan_or(producer.expected_prices.get(arrays.matrices.goods.ids[column])))

    def test_recipe_matrices_hold_the_recipes(self):
        setup, record, view, _ledger, area_map = economy_of(1)
        matrices = YearArrays.build(setup, record, area_map, view).matrices
        for recipe_id, recipe in setup.recipes.items():
            row = matrices.recipes.row[recipe_id]
            for good, quantity in recipe.inputs.items():
                self.assertEqual(matrices.inputs[row, matrices.goods.row[good]], quantity)
            for good, quantity in recipe.outputs.items():
                self.assertEqual(matrices.outputs[row, matrices.goods.row[good]], quantity)
            self.assertEqual(matrices.plant_life_years[row], recipe.plant_life_years)
            self.assertEqual(matrices.goods.ids[matrices.first_output[row]], min(recipe.outputs))

    def test_cohort_columns_hold_the_records(self):
        setup, record, view, _ledger, area_map = economy_of(2)
        cohorts = YearArrays.build(setup, record, area_map, view).cohorts
        for row, cohort_id in enumerate(cohorts.ids):
            cohort = record.cohorts[cohort_id]
            self.assertEqual(cohorts.numeric["people"][row], cohort.people)
            np.testing.assert_equal(cohorts.share_wealth[row], nan_or(cohort.share_wealth))


class SyncFollowsTheTable(unittest.TestCase):
    def test_a_replaced_producer_is_read_again(self):
        setup, record, view, _ledger, area_map = economy_of(3)
        arrays = YearArrays.build(setup, record, area_map, view)
        first = sorted(record.producers)[5]
        record.producers[first] = replace(record.producers[first], capacity_runs=123.5, expected_sales=7.0)
        synced = arrays.sync(setup, record, view)
        self.assertIs(synced.producers, arrays.producers)
        row = synced.producers.row[first]
        self.assertEqual((synced.producers.capacity_runs[row], synced.producers.expected_sales[row]), (123.5, 7.0))

    def test_an_entering_and_a_leaving_producer_rebuild_the_ids(self):
        setup, record, view, _ledger, area_map = economy_of(4)
        arrays = YearArrays.build(setup, record, area_map, view)
        leaving = sorted(record.producers)[0]
        newcomer = replace(record.producers[sorted(record.producers)[1]], agent_id="producer:new")
        del record.producers[leaving]
        record.producers[newcomer.agent_id] = newcomer
        synced = arrays.sync(setup, record, view)
        self.assertEqual(synced.producers.ids, tuple(sorted(record.producers)))
        self.assertNotIn(leaving, synced.producers.row)
        self.assertEqual(synced.producers.capacity_runs[synced.producers.row["producer:new"]], newcomer.capacity_runs)


class MemoryArraysAgreeWithTheMemory(unittest.TestCase):
    def test_prices_kinds_and_wages_are_the_memorys_own_answers(self):
        for seed in range(6):
            setup, record, view, _ledger, area_map = economy_of(seed)
            arrays = YearArrays.build(setup, record, area_map, view)
            memory, tiles = record.memory, arrays.tiles
            for good in GOODS:
                for area in AREAS:
                    key = good + KEY_SEPARATOR + area
                    cell = (arrays.matrices.goods.row[good], arrays.area_index.areas.row[area])
                    np.testing.assert_equal(arrays.memory.price[cell], nan_or(memory.prices.get(key)))
                    np.testing.assert_equal(arrays.memory.offered[cell], nan_or(memory.offered_price(key)))
                    np.testing.assert_equal(arrays.memory.cleared[cell], nan_or(memory.cleared_prices.get(key)))
                    self.assertEqual(bool(arrays.memory.bare_quote[cell]),
                                     memory.price_kind(key) in (QUOTE_BEST_UNFILLED_BID, QUOTE_LOWEST_UNFILLED_ASK))
            for trade in arrays.matrices.trades.ids:
                for tile in TILES:
                    self.assertEqual(arrays.memory.wage[arrays.matrices.trades.row[trade], tiles.row[tile]],
                                     trade_wages.wage_in_view(setup, view, trade, labour_area(tile)))

    def test_the_area_index_is_the_area_maps(self):
        setup, record, view, _ledger, area_map = economy_of(0)
        arrays = YearArrays.build(setup, record, area_map, view)
        for good in GOODS:
            for tile in TILES:
                column = arrays.area_index.of_good_tile[arrays.matrices.goods.row[good], arrays.tiles.row[tile]]
                self.assertNotEqual(column, NO_AREA)
                self.assertEqual(arrays.area_index.areas.ids[column], area_map.area_of(good, tile))


if __name__ == "__main__":
    unittest.main()
