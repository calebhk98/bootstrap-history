"""The harvest weather multiplier is a function of (civilisation, cell, year, salt) and nothing else, so two games and a
reloaded game draw the same year. Called on the real method over a stand-in holding the cells, the correlation and the
salt (no game is built). The seed rule is test_regional_weather_wiring."""
import random
import unittest
from types import SimpleNamespace

from sim import simulator
from sim.engine.core import Sim
from sim.world import agriculture
from sim.world.weather_pooling import correlation_cholesky

QUICK_TOPIC = True

ROME = simulator.load_civ("rome_100ad")
SALT = 424242
CORRELATION_LENGTH_KM = 800.0


def _stand_in(dice_seed, burnt_draws=0):
    """What the pooled multiplier reads: cells, their correlation, the salt, and a game dice that may have been used."""
    dice = random.Random(dice_seed)
    for _draw in range(burnt_draws):
        dice.random()
    stand_in = SimpleNamespace(civ=ROME, world_map=None, rng=dice, _agriculture=agriculture,
                               state=SimpleNamespace(scenario=SimpleNamespace(weather_salt=SALT)))
    stand_in._cap_pooled_farm_weather_cells = lambda cells: Sim._cap_pooled_farm_weather_cells(stand_in, cells)
    stand_in._raw_farm_weather_cells = lambda: Sim._raw_farm_weather_cells(stand_in)
    stand_in._farm_year_weather_seed = lambda year, region=None: Sim._farm_year_weather_seed(stand_in, year, region=region)
    stand_in._farm_weather_cells = Sim._compute_farm_weather_cells(stand_in)
    stand_in._farm_weather_correlation_cholesky = correlation_cholesky(stand_in._farm_weather_cells, CORRELATION_LENGTH_KM)
    return stand_in


class PooledMultiplierIgnoresTheDice(unittest.TestCase):

    def test_the_territory_has_cells_to_pool(self):
        self.assertGreater(len(_stand_in(1)._farm_weather_cells), 1)

    def test_pooled_multiplier_is_the_same_whatever_the_game_dice_did(self):
        fresh, used = _stand_in(1), _stand_in(99, burnt_draws=500)
        for year in range(100, 110):
            self.assertEqual(Sim._pooled_farm_weather_multiplier(fresh, year, harmed=False),
                             Sim._pooled_farm_weather_multiplier(used, year, harmed=False))

    def test_different_years_draw_different_multipliers(self):
        stand_in = _stand_in(1)
        drawn = {Sim._pooled_farm_weather_multiplier(stand_in, year, harmed=False) for year in range(100, 120)}
        self.assertGreater(len(drawn), 15)

    def test_the_tile_multipliers_are_the_same_whatever_the_game_dice_did(self):
        fresh, used = _stand_in(1), _stand_in(99, burnt_draws=500)
        self.assertEqual(Sim.farm_weather_by_tile(fresh, 137), Sim.farm_weather_by_tile(used, 137))


if __name__ == "__main__":
    unittest.main()
