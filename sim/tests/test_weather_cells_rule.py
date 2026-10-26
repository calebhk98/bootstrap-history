"""Complaint 49: the weather cells a civilisation pools its harvest over. `rules.pooled_cells` normalises raw arable-land weights
into shares, and the module's `harvest_weather` falls back to one draw with no cells."""
QUICK_TOPIC = True

import random
import unittest

from sim.agriculture import rules
from sim.tests import agriculture_stand_in
from sim.world import agriculture

CAP = 100


def raw(cell_id, weight):
    return rules.WeatherCell(cell_id=cell_id, lat=40.0, lon=10.0, weight=weight)


class PooledCells(unittest.TestCase):
    def test_weights_become_shares_of_the_arable_land_that_sum_to_one(self):
        cells = rules.pooled_cells([raw("a", 300.0), raw("b", 100.0), raw("c", 600.0)], CAP)
        self.assertEqual([cell.cell_id for cell in cells], ["a", "b", "c"])
        self.assertAlmostEqual(sum(cell.weight for cell in cells), 1.0, places=12)
        self.assertAlmostEqual(cells[0].weight, 0.3)
        self.assertAlmostEqual(cells[2].weight, 0.6)

    def test_with_no_arable_land_anywhere_the_cells_share_equally(self):
        cells = rules.pooled_cells([raw("a", 0.0), raw("b", 0.0)], CAP)
        self.assertEqual([cell.weight for cell in cells], [0.5, 0.5])

    def test_a_civilisation_with_no_land_tiles_gets_no_cells(self):
        self.assertEqual(rules.pooled_cells([], CAP), [])


class PooledFallback(unittest.TestCase):
    def test_with_no_cells_the_whole_territory_draws_one_seeded_multiplier(self):
        year = 137
        farm = agriculture_stand_in.build(rows=[], salt=5)
        expected = agriculture.draw_weather_multiplier(
            random.Random(rules.weather_seed("rome_100ad", None, year, 5)), agriculture.DEFAULT_SOIL.weather_stdev_fraction)
        self.assertEqual(farm.harvest_weather(year), expected)


if __name__ == "__main__":
    unittest.main()
