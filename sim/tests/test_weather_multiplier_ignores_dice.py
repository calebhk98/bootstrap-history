"""The pooled harvest weather multiplier (`Sim._pooled_farm_weather_multiplier`) and the per-cell multipliers
(`Sim.farm_weather_by_tile`) draw each cell from a seed that is a function of (year, cell) alone, so two games and a reloaded
game draw the same year whatever their dice did. Each is called once on a stand-in holding written-out cells, an identity
correlation and a recorder for the seed; the seed rule itself is test_regional_weather_wiring."""
import random
import unittest
from types import SimpleNamespace

from sim.engine.core import Sim
from sim.world import agriculture

QUICK_TOPIC = True

CELLS = [Sim._WeatherCell("t1", 40.0, 10.0, 3.0), Sim._WeatherCell("t2", 41.0, 12.0, 1.0)]
IDENTITY = [[1.0, 0.0], [0.0, 1.0]]


def stand_in(dice_seed, burnt_draws=0, seeds_asked=None):
    dice = random.Random(dice_seed)
    for _draw in range(burnt_draws):
        dice.random()

    def seed(year, region=None):
        if seeds_asked is not None:
            seeds_asked.append((year, region))
        return year * 1000 + (1 if region == "t1" else 2)
    return SimpleNamespace(rng=dice, _agriculture=agriculture, _farm_weather_cells=list(CELLS),
                           _farm_weather_correlation_cholesky=IDENTITY, _farm_year_weather_seed=seed)


class PooledMultiplier(unittest.TestCase):

    def test_it_is_the_same_whatever_the_game_dice_did(self):
        for year in range(100, 105):
            self.assertEqual(Sim._pooled_farm_weather_multiplier(stand_in(1), year, harmed=False),
                             Sim._pooled_farm_weather_multiplier(stand_in(99, burnt_draws=500), year, harmed=False))

    def test_each_cell_is_drawn_from_the_seed_of_that_year_and_cell(self):
        asked = []
        Sim._pooled_farm_weather_multiplier(stand_in(1, seeds_asked=asked), 137, harmed=False)
        self.assertEqual(asked, [(137, "t1"), (137, "t2")])

    def test_different_years_draw_different_multipliers(self):
        drawn = {Sim._pooled_farm_weather_multiplier(stand_in(1), year, harmed=False) for year in range(100, 120)}
        self.assertGreater(len(drawn), 15)

    def test_with_no_cells_it_falls_back_to_one_draw_seeded_by_the_year_alone(self):
        asked = []
        game = stand_in(1, seeds_asked=asked)
        game._farm_weather_cells = []
        Sim._pooled_farm_weather_multiplier(game, 137, harmed=False)
        self.assertEqual(asked, [(137, None)])


class MultipliersByTile(unittest.TestCase):

    def test_they_are_the_same_whatever_the_game_dice_did(self):
        self.assertEqual(Sim.farm_weather_by_tile(stand_in(1), 137), Sim.farm_weather_by_tile(stand_in(99, burnt_draws=500), 137))

    def test_every_cell_has_a_multiplier(self):
        self.assertEqual(sorted(Sim.farm_weather_by_tile(stand_in(1), 137)), ["t1", "t2"])


if __name__ == "__main__":
    unittest.main()
