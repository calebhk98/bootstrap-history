"""What siting reads of the map and the producers (entry_siting_tables.py): each function against the loop it replaced, on inputs
written out. Values must be equal to the last bit (they feed a discrete choice of tile)."""

QUICK_TOPIC = True

import math
import types
import unittest

import numpy as np

from sim.economy import entry_siting_tables as tables
from sim.economy.types import Recipe, SiteLimit

TILES = ("T0", "T1", "T2")
ROW = {tile: position for position, tile in enumerate(TILES)}


class SearchedCarriage:
    """A carriage table that searches costs once and scales them, as tile_costs.CarriageTable does."""

    def __init__(self, scale):
        self.scale = scale
        self.searches = 0
        self.unscaled = {"T0": {"T0": 0.0, "T1": 2.5, "T2": 7.1}, "T1": {"T1": 0.0, "T0": 2.5}, "T2": {"T2": 0.0, "T0": 7.1, "OUTSIDE": 1.0}}

    def unscaled_costs_from(self, source):
        self.searches += 1
        return self.unscaled[source]

    def costs_from(self, source):
        return {tile: cost * self.scale for tile, cost in self.unscaled[source].items()}


class CarriageMatrixIsTheLoop(unittest.TestCase):
    def old_matrix(self, carriage):
        matrix = np.full((3, 3), np.inf)
        for source in TILES:
            for tile, cost in carriage.costs_from(source).items():
                column = ROW.get(tile)
                if column is not None:
                    matrix[ROW[source], column] = cost
        return matrix

    def test_a_scaled_table_gives_the_scaled_costs_and_unreached_pairs_stay_infinite(self):
        carriage = SearchedCarriage(1.3)
        np.testing.assert_array_equal(tables.carriage_matrix(carriage, TILES, ROW), self.old_matrix(carriage))

    def test_a_table_at_scale_one_gives_the_searched_costs(self):
        carriage = SearchedCarriage(1.0)
        np.testing.assert_array_equal(tables.carriage_matrix(carriage, TILES, ROW), self.old_matrix(carriage))

    def test_the_costs_are_searched_once_for_one_table_and_the_scale_applies_each_time(self):
        carriage = SearchedCarriage(1.0)
        tables.carriage_matrix(carriage, TILES, ROW)
        carriage.scale = 2.0
        second = tables.carriage_matrix(carriage, TILES, ROW)
        self.assertEqual(carriage.searches, len(TILES))
        np.testing.assert_array_equal(second, self.old_matrix(carriage))

    def test_a_table_without_searched_costs_is_read_by_its_costs(self):
        class Plain:
            def cost_per_tonne(self, source, tile):
                return abs(ROW[source] - ROW[tile]) * 1.5
        plain = Plain()
        expected = np.array([[abs(first - second) * 1.5 for second in range(3)] for first in range(3)])
        np.testing.assert_array_equal(tables.carriage_matrix(plain, TILES, ROW), expected)


def columns_of(recipe_rows, records, caps, recipe_ids):
    return types.SimpleNamespace(
        recipe_row=np.array(recipe_rows, dtype=np.int64), records=records, land_run_cap=np.array(caps),
        matrices=types.SimpleNamespace(recipes=types.SimpleNamespace(ids=recipe_ids)))


class ProducerReads(unittest.TestCase):
    def test_hours_are_the_booked_hours_unless_the_crew_has_practice(self):
        recipes = {"a": Recipe("a", {}, {"x": 1.0}, {"labourer": 2.0, "smith": 0.1}),
                   "b": Recipe("b", {}, {"y": 1.0}, {"labourer": 3.0})}
        records = [types.SimpleNamespace(recipe_id="a", crew_runs={}), types.SimpleNamespace(recipe_id="b", crew_runs={}),
                   types.SimpleNamespace(recipe_id="b", crew_runs={"labourer": 1.0})]
        columns = columns_of([0, 1, 1], records, [np.nan] * 3, ["a", "b"])
        hours = tables.hours_of_producers(recipes, columns)
        self.assertEqual(hours[0], math.fsum([2.0, 0.1]))
        self.assertEqual(hours[1], 3.0)
        self.assertGreater(hours[2], 3.0)         # a crew at its first run takes more hours than the booked ones

    def test_a_land_short_producer_takes_land_and_has_a_stated_cap(self):
        columns = columns_of([0, 0, 1, 1], [], [np.nan, 5.0, 5.0, np.nan], ["a", "b"])
        rows = tables.land_short_rows(columns, np.array([0.5, 0.0]))
        self.assertEqual(rows.tolist(), [1])


class YieldAndLimitAreTheLoops(unittest.TestCase):
    def test_yield_follows_the_limit_for_a_site_bound_recipe_else_the_factor(self):
        limits = {"T0": SiteLimit("dig", "T0", 40.0, 1.2), "T2": SiteLimit("dig", "T2", 15.0, 0.9), "T9": SiteLimit("dig", "T9", 1.0, 5.0)}
        factors = {"dig@T1": 0.8, "dig@T0": 3.0, "other@T1": 9.0}
        bound = Recipe("dig", {}, {"x": 1.0}, {"labourer": 1.0}, site_bound=True)
        free = Recipe("dig", {}, {"x": 1.0}, {"labourer": 1.0})
        self.assertEqual(tables.yield_row(bound, TILES, factors, limits, ROW).tolist(), [1.2, 0.8, 0.9])
        self.assertEqual(tables.yield_row(free, TILES, factors, limits, ROW).tolist(), [3.0, 0.8, 1.0])

    def test_the_limit_row_has_the_capacity_where_a_limit_is_stated_and_nothing_elsewhere(self):
        limits = {"T0": SiteLimit("dig", "T0", 40.0, 1.2), "T2": SiteLimit("dig", "T2", 15.0, 0.9), "T9": SiteLimit("dig", "T9", 1.0, 5.0)}
        self.assertEqual(tables.limit_row(limits, TILES, ROW).tolist(), [40.0, 0.0, 15.0])


if __name__ == "__main__":
    unittest.main()
