"""The stability phase's per-tile kernel gives, bit for bit, what the plain rule functions give a tile at a time."""

QUICK_TOPIC = True

import random
import unittest

import numpy as np

from sim.campaigns import stability_tiles
from sim.campaigns.stability_kernels import TILE_COLUMNS
from sim.geography.api import settlement
from sim.tests.stability_tiles_plain import plain_tile


def random_columns(rng, count):
    """Columns for `count` tiles: some without food booked (NaN), some without a garrison, some with nobody left to pay."""
    columns = {
        "people": [rng.choice([0.0, rng.uniform(1.0, 5000.0)]) for _ in range(count)],
        "land_taken": [rng.choice([0.0, rng.uniform(0.0, 2.0)]) for _ in range(count)],
        "eaten_over_need": [rng.choice([float("nan"), 0.0, 1.0, 1.3, rng.uniform(0.0, 1.2)]) for _ in range(count)],
        "garrison_soldiers": [rng.choice([0.0, rng.uniform(0.5, 800.0)]) for _ in range(count)],
        "garrison_equipment": [rng.uniform(0.0, 90.0) for _ in range(count)],
        "garrison_supply": [rng.uniform(0.0, 1.2) for _ in range(count)],
        "ruggedness": [rng.uniform(-0.1, 4.0) for _ in range(count)],
        "fortification": [rng.choice([0.0, rng.uniform(0.0, 1.5)]) for _ in range(count)],
    }
    columns["registered"] = [max(people, rng.uniform(0.0, 6000.0)) for people in columns["people"]]
    return {name: np.array(values) for name, values in columns.items()}


class ReadTilesTests(unittest.TestCase):
    def test_the_kernel_gives_what_the_plain_rules_give_each_tile(self):
        rng = random.Random(7)
        for collective in (False, True):
            columns = random_columns(rng, 300)
            felt, rate, organised, reference = rng.uniform(0.0, 1.0), rng.uniform(0.0, 0.5), rng.uniform(0.1, 1.0), 31.0
            got = stability_tiles.read_tiles(columns, felt, collective, rate, organised, reference)
            for tile in range(300):
                values = [float(columns[name][tile]) for name in TILE_COLUMNS]
                values[3] = None if np.isnan(values[3]) else values[3]
                expected = plain_tile(*values, felt, collective, rate, organised, reference)
                self.assertEqual(tuple(float(column[tile]) for column in got[:5]), tuple(expected[:5]), tile)
                self.assertEqual(bool(got[5][tile]), expected[5], tile)

    def test_a_reference_equipment_that_is_not_positive_is_refused(self):
        columns = random_columns(random.Random(1), 3)
        with self.assertRaises(ValueError):
            stability_tiles.read_tiles(columns, 0.1, False, 0.1, 0.5, 0.0)


class GarrisonColumnsTests(unittest.TestCase):
    def test_free_soldiers_are_shared_by_the_tiles_people_and_a_tile_with_none_has_none(self):
        owned = ["a", "b", "c"]
        shares = settlement.population_shares(owned)
        soldiers, equipment, supply = stability_tiles.garrison_columns(["a", "b", "elsewhere"], owned, 120.0, 12.0, {})
        self.assertEqual(float(soldiers[0]), 120.0 * shares["a"])
        self.assertEqual((float(soldiers[2]), float(equipment[2]), float(supply[2])), (0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
