"""Complaint 537: the agriculture module's `farm_weather` and `harvest_weather` read the same draws from the civilisation's
weather cells, so the weight-average of the per-tile values is the pooled multiplier the national path reads. Both are called
on the module built over written-out tiles; the arithmetic is test_weather_cells."""
QUICK_TOPIC = True

import unittest

from sim.tests import agriculture_stand_in

YEAR = 100

# a pair of near tiles and a far one; weights are land area times arable fraction: 500, 300 and 200
ROWS = [("near_a", 40.0, 10.0, 1000.0, 0.5), ("near_b", 40.5, 10.0, 1000.0, 0.3), ("far", 10.0, 80.0, 1000.0, 0.2)]


class TileWeatherWiring(unittest.TestCase):
    def test_the_weighted_mean_of_the_tiles_is_the_pooled_multiplier(self):
        farm = agriculture_stand_in.build(ROWS)
        by_tile = farm.farm_weather(YEAR)
        weights = {cell.cell_id: cell.weight for cell in farm.weather_cells()}
        mean = sum(weights[tile_id] * value for tile_id, value in by_tile.items())
        self.assertAlmostEqual(mean, farm.harvest_weather(YEAR, harmed=False), places=9)

    def test_a_year_repeats_and_the_next_year_draws_again(self):
        farm = agriculture_stand_in.build(ROWS)
        first = farm.farm_weather(YEAR)
        self.assertEqual(first, farm.farm_weather(YEAR))
        self.assertNotEqual(first, farm.farm_weather(YEAR + 1))

    def test_a_civilisation_with_no_cells_has_no_per_tile_weather(self):
        self.assertEqual(agriculture_stand_in.build([]).farm_weather(YEAR), {})


if __name__ == "__main__":
    unittest.main()
