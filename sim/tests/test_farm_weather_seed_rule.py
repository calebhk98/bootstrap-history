"""The harvest weather's seed is a pure function of the civilisation id, the region, the year and the game's weather
salt, so a reloaded game retraces the same weather (Sim._farm_year_weather_seed). Called on stand-ins."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

from sim.engine.core import Sim


def _game(civ_id="rome_100ad", salt=12345, rng_seed=1):
    return SimpleNamespace(civ={"id": civ_id}, state=SimpleNamespace(scenario=SimpleNamespace(weather_salt=salt)),
                           rng=random.Random(rng_seed))


def _seed(game, year, region=None):
    return Sim._farm_year_weather_seed(game, year, region)


class WeatherSeedIsPure(unittest.TestCase):

    def test_two_games_with_one_salt_draw_one_seed_whatever_their_dice_or_the_order_asked(self):
        first, second = _game(rng_seed=1), _game(rng_seed=99)
        _seed(first, 110)
        _seed(first, 105)
        self.assertEqual(_seed(first, 107, "italy_02"), _seed(second, 107, "italy_02"))
        self.assertEqual(_seed(first, 107), _seed(second, 107))

    def test_a_game_without_a_salt_draws_it_once_from_its_dice_and_keeps_it(self):
        game = _game(salt=0)
        seed = _seed(game, 101)
        self.assertGreater(game.state.scenario.weather_salt, 0)
        self.assertEqual(_seed(game, 101), seed)
        self.assertEqual(_seed(_game(salt=0), 101), seed)

    def test_year_region_civilisation_and_salt_each_change_the_seed(self):
        game = _game()
        seeds = {_seed(game, 101), _seed(game, 102), _seed(game, 101, "italy_02"), _seed(game, 101, "italy_03"),
                 _seed(_game(civ_id="han_china_100ad"), 101), _seed(_game(salt=777), 101)}
        self.assertEqual(len(seeds), 6)


if __name__ == "__main__":
    unittest.main()
