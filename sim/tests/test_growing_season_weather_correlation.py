"""Growing-season weather is correlated by distance (Complaints/49-one-label-draws-one-coin.md): weather agrees with itself
over a distance, so two nearby cells draw nearly the same year and two cells continents apart draw independently, and a
territory spread over many cells pools to a steadier harvest than one cell would. The rules, on cells the test builds
(`sim/world/weather_pooling.py`); the cell weights are in test_weather_cells_rule."""
import collections
import math
import random
import statistics
import unittest

from sim.world import agriculture
from sim.world.shared_constants import GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM
from sim.world.weather_pooling import chordal_position_km, correlation_cholesky, pooled_multiplier

QUICK_TOPIC = True

Cell = collections.namedtuple("Cell", "cell_id lat lon weight")
LENGTH_KM = GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM


def correlation_from_cholesky(lower):
    dimension = len(lower)
    return [[sum(lower[row][term] * lower[col][term] for term in range(min(row, col) + 1))
             for col in range(dimension)] for row in range(dimension)]


class SpatialCorrelationTests(unittest.TestCase):

    def test_cholesky_factor_reproduces_the_intended_correlation_matrix(self):
        cells = [Cell("a", 41.0, 12.0, 0.5), Cell("b", 42.0, 13.0, 0.3), Cell("c", -10.0, 140.0, 0.2)]
        rebuilt = correlation_from_cholesky(correlation_cholesky(cells, LENGTH_KM))
        for row in range(3):
            self.assertAlmostEqual(rebuilt[row][row], 1.0, places=6)
        # a and b are about 150 km apart; c is across the planet
        self.assertGreater(rebuilt[0][1], rebuilt[0][2])
        self.assertGreater(rebuilt[1][0], rebuilt[1][2])
        self.assertAlmostEqual(rebuilt[0][1], rebuilt[1][0], places=9)

    def test_the_correlation_is_the_exponential_of_the_chordal_distance(self):
        cells = [Cell("a", 41.0, 12.0, 0.5), Cell("b", 48.0, 2.0, 0.5)]
        rebuilt = correlation_from_cholesky(correlation_cholesky(cells, LENGTH_KM))
        a, b = chordal_position_km(41.0, 12.0), chordal_position_km(48.0, 2.0)
        distance = sum((first - second) ** 2 for first, second in zip(a, b)) ** 0.5
        self.assertAlmostEqual(rebuilt[0][1], math.exp(-distance / LENGTH_KM), places=9)

    def test_neighbouring_regions_share_weather_far_more_than_distant_ones(self):
        # Gaul and Hispania share weather systems; Britannia and the Levant do not
        cells = [Cell("gaul", 46.6, 2.5, 0.25), Cell("hispania", 40.4, -3.7, 0.25),
                 Cell("britannia", 52.5, -1.5, 0.25), Cell("levant", 33.5, 38.0, 0.25)]
        rebuilt = correlation_from_cholesky(correlation_cholesky(cells, LENGTH_KM))
        gaul_hispania, britannia_levant = rebuilt[0][1], rebuilt[2][3]
        self.assertGreater(gaul_hispania, 2 * britannia_levant, (gaul_hispania, britannia_levant))

    def test_a_cell_perfectly_correlates_with_itself(self):
        lower = correlation_cholesky([Cell("solo", 10.0, 20.0, 1.0)], LENGTH_KM)
        self.assertAlmostEqual(lower[0][0], 1.0, places=9)

    def test_a_longer_decorrelation_length_correlates_the_same_cells_more(self):
        cells = [Cell("a", 41.0, 12.0, 0.5), Cell("b", 48.0, 2.0, 0.5)]
        short = correlation_from_cholesky(correlation_cholesky(cells, 100.0))[0][1]
        long = correlation_from_cholesky(correlation_cholesky(cells, 3000.0))[0][1]
        self.assertGreater(long, short)

    def test_the_factor_is_lower_triangular(self):
        cells = [Cell(str(index), 30.0 + index, 10.0 * index, 0.25) for index in range(4)]
        lower = correlation_cholesky(cells, LENGTH_KM)
        for row in range(4):
            for col in range(row + 1, 4):
                self.assertEqual(lower[row][col], 0.0)


class PooledMultiplierTests(unittest.TestCase):

    FLOOR, CEILING, STDEV = agriculture.WEATHER_FLOOR_MULTIPLIER, agriculture.WEATHER_CEILING_MULTIPLIER, \
        agriculture.WEATHER_YIELD_STDEV_FRACTION

    def _spread_cells(self, count):
        return [Cell(str(index), 20.0 + 1.5 * index, 5.0 + 4.0 * index, 1.0 / count) for index in range(count)]

    def _pooled_draws(self, cells, years=1000):
        lower = correlation_cholesky(cells, LENGTH_KM)
        draws = []
        for year in range(years):
            independent = [random.Random(year * 1000 + index).gauss(0.0, 1.0) for index in range(len(cells))]
            draws.append(pooled_multiplier(cells, lower, independent, self.STDEV, self.FLOOR, self.CEILING))
        return draws

    def test_zero_draws_pool_to_the_mean_weather(self):
        cells = self._spread_cells(5)
        lower = correlation_cholesky(cells, LENGTH_KM)
        self.assertAlmostEqual(pooled_multiplier(cells, lower, [0.0] * 5, self.STDEV, self.FLOOR, self.CEILING), 1.0)

    def test_a_territory_spread_over_many_cells_is_steadier_than_one_cell(self):
        # the bug in Complaints/49: a large region used to draw one coin, like a small one
        spread = statistics.pstdev(self._pooled_draws(self._spread_cells(40)))
        single = statistics.pstdev(self._pooled_draws([Cell("solo", 40.0, 10.0, 1.0)]))
        self.assertLess(spread, single * 0.85, (spread, single))

    def test_a_single_cell_draws_at_the_stated_spread(self):
        single = statistics.pstdev(self._pooled_draws([Cell("solo", 40.0, 10.0, 1.0)]))
        self.assertAlmostEqual(single, self.STDEV, delta=0.03)

    def test_each_cell_is_clipped_before_the_average(self):
        cells = [Cell("a", 40.0, 10.0, 0.5), Cell("b", 40.0, 10.0, 0.5)]
        lower = [[1.0, 0.0], [0.0, 1.0]]
        extreme = pooled_multiplier(cells, lower, [100.0, -100.0], self.STDEV, self.FLOOR, self.CEILING)
        self.assertAlmostEqual(extreme, 0.5 * self.CEILING + 0.5 * self.FLOOR)

    def test_the_weights_decide_each_cells_share(self):
        cells = [Cell("a", 40.0, 10.0, 0.75), Cell("b", 40.0, 10.0, 0.25)]
        lower = [[1.0, 0.0], [0.0, 1.0]]
        pooled = pooled_multiplier(cells, lower, [1.0, -1.0], 0.1, self.FLOOR, self.CEILING)
        self.assertAlmostEqual(pooled, 0.75 * 1.1 + 0.25 * 0.9)


if __name__ == "__main__":
    unittest.main()
