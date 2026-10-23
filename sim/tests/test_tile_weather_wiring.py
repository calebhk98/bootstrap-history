"""Complaint 537: `Sim.farm_weather_by_tile` and `Sim._pooled_farm_weather_multiplier` read the same draws from the
civilisation's weather cells, so the weight-average of the per-tile values is the pooled multiplier the national path reads.
Each method is called on a stand-in `self` carrying only the cells, the seed rule and the agriculture constants; the
arithmetic is test_weather_cells."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine.core import Sim
from sim.world import agriculture
from sim.world.weather_pooling import correlation_cholesky

YEAR = 100


def stand_in_game():
    cells = [SimpleNamespace(cell_id="near_a", lat=40.0, lon=10.0, weight=0.5),
             SimpleNamespace(cell_id="near_b", lat=40.5, lon=10.0, weight=0.3),
             SimpleNamespace(cell_id="far", lat=10.0, lon=80.0, weight=0.2)]
    return SimpleNamespace(
        _farm_weather_cells=cells,
        _farm_weather_correlation_cholesky=correlation_cholesky(cells, 500.0),
        _farm_year_weather_seed=lambda year, region=None: "%s/%s" % (year, region),
        _agriculture=agriculture)


class TileWeatherWiring(unittest.TestCase):
    def test_the_weighted_mean_of_the_tiles_is_the_pooled_multiplier(self):
        game = stand_in_game()
        by_tile = Sim.farm_weather_by_tile(game, YEAR)
        weights = {cell.cell_id: cell.weight for cell in game._farm_weather_cells}
        mean = sum(weights[tile_id] * value for tile_id, value in by_tile.items())
        self.assertAlmostEqual(mean, Sim._pooled_farm_weather_multiplier(game, YEAR, harmed=False), places=9)

    def test_a_year_repeats_and_the_next_year_draws_again(self):
        game = stand_in_game()
        first = Sim.farm_weather_by_tile(game, YEAR)
        self.assertEqual(first, Sim.farm_weather_by_tile(game, YEAR))
        self.assertNotEqual(first, Sim.farm_weather_by_tile(game, YEAR + 1))

    def test_a_civilisation_with_no_cells_has_no_per_tile_weather(self):
        game = stand_in_game()
        game._farm_weather_cells = []
        self.assertEqual(Sim.farm_weather_by_tile(game, YEAR), {})


if __name__ == "__main__":
    unittest.main()
