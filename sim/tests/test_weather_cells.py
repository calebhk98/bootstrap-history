"""Complaint 537: the pooled harvest multiplier is the weight-average of the cells' own multipliers, which are what each
tile's yield now reads. Called on cells built in the test (growing-season correlation itself is
test_growing_season_weather_correlation)."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.world.weather_pooling import cell_multipliers, correlation_cholesky, pooled_multiplier

FLOOR, CEILING, STDEV = 0.4, 1.6, 0.2
DECORRELATION_KM = 500.0


def cells():
    return [SimpleNamespace(cell_id="near_a", lat=40.0, lon=10.0, weight=0.5),
            SimpleNamespace(cell_id="near_b", lat=40.5, lon=10.0, weight=0.3),
            SimpleNamespace(cell_id="far", lat=10.0, lon=80.0, weight=0.2)]


class CellMultiplierTests(unittest.TestCase):
    def setUp(self):
        self.cells = cells()
        self.cholesky = correlation_cholesky(self.cells, DECORRELATION_KM)
        self.draws = [1.5, -0.5, -1.2]

    def multipliers(self, draws=None):
        return cell_multipliers(self.cells, self.cholesky, draws or self.draws, STDEV, FLOOR, CEILING)

    def test_the_pooled_multiplier_is_the_weighted_mean_of_the_cells(self):
        pooled = pooled_multiplier(self.cells, self.cholesky, self.draws, STDEV, FLOOR, CEILING)
        self.assertAlmostEqual(pooled, sum(cell.weight * value for cell, value in zip(self.cells, self.multipliers())), places=12)

    def test_cells_differ_so_a_bad_year_on_one_tile_is_not_every_tiles(self):
        values = self.multipliers()
        self.assertGreater(max(values) - min(values), 0.05)

    def test_a_distant_cell_follows_its_own_draw_and_a_neighbour_follows_the_first(self):
        high_first = self.multipliers([2.0, 0.0, 0.0])
        self.assertGreater(high_first[1], 1.0)          # the neighbour shares most of the first cell's weather
        self.assertAlmostEqual(high_first[2], 1.0, delta=0.01)   # the far cell does not

    def test_every_multiplier_is_held_to_the_floor_and_ceiling(self):
        for value in self.multipliers([40.0, -40.0, 40.0]):
            self.assertTrue(FLOOR <= value <= CEILING)


if __name__ == "__main__":
    unittest.main()
