"""Complaint 49: the weather cells a civilisation pools its harvest over. `Sim._compute_farm_weather_cells` normalises raw
arable-land weights into shares, and `Sim._pooled_farm_weather_multiplier` falls back to one draw with no cells; both are
called here on a stand-in that holds only what they read."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

from sim.engine.core import Sim
from sim.world import agriculture


def cells_of(raw_cells):
    stand_in = SimpleNamespace(_raw_farm_weather_cells=lambda: raw_cells, _cap_pooled_farm_weather_cells=lambda cells: cells)
    return Sim._compute_farm_weather_cells(stand_in)


def raw(cell_id, weight):
    return Sim._WeatherCell(cell_id=cell_id, lat=40.0, lon=10.0, weight=weight)


class ComputeCells(unittest.TestCase):
    def test_weights_become_shares_of_the_arable_land_that_sum_to_one(self):
        cells = cells_of([raw("a", 300.0), raw("b", 100.0), raw("c", 600.0)])
        self.assertEqual([cell.cell_id for cell in cells], ["a", "b", "c"])
        self.assertAlmostEqual(sum(cell.weight for cell in cells), 1.0, places=12)
        self.assertAlmostEqual(cells[0].weight, 0.3)
        self.assertAlmostEqual(cells[2].weight, 0.6)

    def test_with_no_arable_land_anywhere_the_cells_share_equally(self):
        cells = cells_of([raw("a", 0.0), raw("b", 0.0)])
        self.assertEqual([cell.weight for cell in cells], [0.5, 0.5])

    def test_a_civilisation_with_no_land_tiles_gets_no_cells(self):
        self.assertEqual(cells_of([]), [])


class PooledFallback(unittest.TestCase):
    def test_with_no_cells_the_whole_territory_draws_one_seeded_multiplier(self):
        year = 137
        stand_in = SimpleNamespace(_agriculture=agriculture, _farm_weather_cells=[],
                                   _farm_year_weather_seed=lambda draw_year, region=None: draw_year * 31)
        expected = agriculture.draw_weather_multiplier(random.Random(year * 31), agriculture.DEFAULT_SOIL.weather_stdev_fraction)
        self.assertEqual(Sim._pooled_farm_weather_multiplier(stand_in, year), expected)


if __name__ == "__main__":
    unittest.main()
