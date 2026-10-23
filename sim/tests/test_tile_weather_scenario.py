"""SCENARIO (Complaint 537): in a running game each held tile has a weather multiplier of its own (the farm weather cell it
stands in), and the arable-weighted mean of them is the pooled multiplier the national path reads. The arithmetic is
test_weather_cells; how a producer reads it is test_economy_crop_yields."""
import unittest

from .harness import *  # noqa: F401,F403

YEAR = 100


class TileWeatherInAGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = unopened_sim(civ="rome_100ad")

    def test_the_arable_weighted_mean_of_the_tiles_is_the_pooled_multiplier(self):
        by_tile = self.game.farm_weather_by_tile(YEAR)
        weights = {cell.cell_id: cell.weight for cell in self.game._farm_weather_cells}
        mean = sum(weights[tile_id] * value for tile_id, value in by_tile.items())
        self.assertAlmostEqual(mean, self.game._pooled_farm_weather_multiplier(YEAR, harmed=False), places=9)

    def test_tiles_differ_in_a_year_and_a_year_repeats(self):
        first = self.game.farm_weather_by_tile(YEAR)
        self.assertGreater(max(first.values()) - min(first.values()), 0.02)
        self.assertEqual(first, self.game.farm_weather_by_tile(YEAR))
        self.assertNotEqual(first, self.game.farm_weather_by_tile(YEAR + 1))


if __name__ == "__main__":
    unittest.main()
