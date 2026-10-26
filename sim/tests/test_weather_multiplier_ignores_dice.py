"""The pooled harvest weather multiplier (`harvest_weather`) and the per-cell multipliers (`farm_weather`) of the agriculture
module draw each cell from a seed that is a function of (year, cell, the game's salt) alone, so two games with one salt and a
reloaded game draw the same year whatever their dice did. Each is called on the module built over written-out tiles; the seed
rule itself is test_regional_weather_wiring."""
import unittest

from sim.tests import agriculture_stand_in

QUICK_TOPIC = True

ROWS = [("t1", 40.0, 10.0, 1000.0, 0.3), ("t2", 41.0, 12.0, 1000.0, 0.1)]


class PooledMultiplier(unittest.TestCase):

    def test_it_is_the_same_whatever_the_game_dice_did(self):
        for year in range(100, 105):
            self.assertEqual(agriculture_stand_in.build(ROWS, dice_seed=1).harvest_weather(year, harmed=False),
                             agriculture_stand_in.build(ROWS, dice_seed=99, burnt_draws=500).harvest_weather(year, harmed=False))

    def test_different_years_draw_different_multipliers(self):
        farm = agriculture_stand_in.build(ROWS)
        self.assertGreater(len({farm.harvest_weather(year, harmed=False) for year in range(100, 120)}), 15)

    def test_with_no_cells_it_falls_back_to_one_draw_seeded_by_the_year_alone(self):
        farm = agriculture_stand_in.build([])
        self.assertEqual(farm.harvest_weather(137, harmed=False), agriculture_stand_in.build([]).harvest_weather(137, harmed=False))
        self.assertNotEqual(farm.harvest_weather(137, harmed=False), farm.harvest_weather(138, harmed=False))


class MultipliersByTile(unittest.TestCase):

    def test_they_are_the_same_whatever_the_game_dice_did(self):
        self.assertEqual(agriculture_stand_in.build(ROWS, dice_seed=1).farm_weather(137),
                         agriculture_stand_in.build(ROWS, dice_seed=99, burnt_draws=500).farm_weather(137))

    def test_every_cell_has_a_multiplier(self):
        self.assertEqual(sorted(agriculture_stand_in.build(ROWS).farm_weather(137)), ["t1", "t2"])


if __name__ == "__main__":
    unittest.main()
