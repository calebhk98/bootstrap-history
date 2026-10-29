"""The harvest weather's seed is a pure function of the civilisation id, the region, the year and the game's weather salt, so a
reloaded game retraces the same weather (`rules.weather_seed`); the module draws the salt once from the game's dice at the
first seed asked for (`Agriculture.weather_seed`), and each cell is drawn from its own seed in cell order
(`rules.independent_draws`)."""
QUICK_TOPIC = True

import random
import unittest

from sim.agriculture import rules
from sim.tests import agriculture_stand_in


def _seed(civ_id="rome_100ad", salt=12345, year=101, region=None):
    return rules.weather_seed(civ_id, region, year, salt)


class WeatherSeedIsPure(unittest.TestCase):

    def test_one_salt_gives_one_seed_whatever_the_order_asked(self):
        self.assertEqual(_seed(year=107, region="italy_02"), _seed(year=107, region="italy_02"))
        self.assertEqual(rules.weather_seed("rome_100ad", None, 107, 12345), (
            sum((index + 1) * ord(character) for index, character in enumerate("rome_100ad")) * 1000003 + 107 * 97 + 12345 * 104729)
            % (2 ** 32))

    def test_year_region_civilisation_and_salt_each_change_the_seed(self):
        seeds = {_seed(), _seed(year=102), _seed(region="italy_02"), _seed(region="italy_03"),
                 _seed(civ_id="han_china_100ad"), _seed(salt=777)}
        self.assertEqual(len(seeds), 6)


class SaltFromTheDice(unittest.TestCase):

    def test_a_game_without_a_salt_draws_it_once_from_its_dice_and_keeps_it(self):
        farm = agriculture_stand_in.build(salt=0)
        seed = farm.weather_seed(101)
        self.assertGreater(farm.world.weather_salt, 0)
        self.assertEqual(farm.weather_seed(101), seed)
        self.assertEqual(agriculture_stand_in.build(salt=0).weather_seed(101), seed)

    def test_another_game_dice_gives_another_salt(self):
        self.assertNotEqual(agriculture_stand_in.build(salt=0, dice_seed=1).weather_seed(101),
                            agriculture_stand_in.build(salt=0, dice_seed=2).weather_seed(101))

    def test_a_salted_game_leaves_its_dice_alone(self):
        farm = agriculture_stand_in.build(salt=5, dice_seed=3)
        farm.weather_seed(101)
        self.assertEqual(farm.needs.game_random().random(), random.Random(3).random())


class IndependentDraws(unittest.TestCase):

    def test_each_cell_is_drawn_from_the_seed_of_its_own_id_in_cell_order(self):
        asked = []
        cells = [rules.WeatherCell("t1", 40.0, 10.0, 0.5), rules.WeatherCell("t2", 41.0, 12.0, 0.5)]
        draws = rules.independent_draws(cells, lambda cell_id: asked.append(cell_id) or ord(cell_id[-1]))
        self.assertEqual(asked, ["t1", "t2"])
        self.assertEqual(len(draws), 2)


if __name__ == "__main__":
    unittest.main()
