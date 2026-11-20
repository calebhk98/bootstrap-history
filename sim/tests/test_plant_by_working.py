"""The plant a producer replaces and adds under the clearing rule set (`close_run.close_producers` with the clearing
set's weight on the runs worked): the plant it wants is its capacity moved toward the capacity the runs it worked call
for (capacity_by_working.py), and what wear and losses leave short of that is rebuilt, up to the wear from its own coin.
Random economies of year_close_fixture, no game."""

QUICK_TOPIC = True

import unittest
from unittest import mock

import numpy as np

from sim.economy import close_pack, producers
from sim.economy.ask_ceiling import AskAlternatives
from sim.economy.capacity_by_working import CAPACITY_SHARE_MOVED_PER_YEAR, capacity_toward_working
from sim.economy.close_kernel import K_CHANGE, K_INERTIA, K_SPREAD, K_WORKING_SHARE, K_WORKING_WEIGHT
from sim.economy.close_run import close_producers
from sim.economy.year_arrays import YearArrays
from sim.tests.year_close_fixture import economy_of

SEEDS = range(6)


def band_above_cost(_alternatives, good, tile):
    """The width of the band above cost the buyers give, a fixed figure per good and tile in place of the year's prices."""
    return 1.0 + (len(good) + len(tile)) % 4 * 0.75


def closed(seed, weight, with_rates=True):
    """(year arrays, the close's answer, its constants) of a random economy, the weight on the runs worked as given;
    without rates no producer can reckon a charge on its plant."""
    setup, record, view, ledger, area_map = economy_of(seed, producer_count=60)
    arrays = YearArrays.build(setup, record, area_map, view)
    constants = close_pack.constants_array()
    constants[K_WORKING_WEIGHT] = weight
    constants[K_WORKING_SHARE] = CAPACITY_SHARE_MOVED_PER_YEAR
    with mock.patch.object(AskAlternatives, "multiple", band_above_cost):
        pack = close_pack.pack(setup, record, view, ledger, arrays)
        if not with_rates:
            pack.rate_of[:] = np.nan
        return arrays, close_producers(arrays, pack, None, constants), constants


def plant_rows(arrays, answer):
    life = arrays.matrices.plant_life_years[arrays.producers.recipe_row]
    return np.flatnonzero((life > 0.0) & (arrays.producers.idle_years <= 0) & ~answer.exited), life


class PlantWantedFollowsTheRunsWorked(unittest.TestCase):
    def test_with_no_rate_the_plant_rebuilt_is_what_wear_left_short_of_the_capacity_the_runs_worked_call_for(self):
        compared = rebuilt = 0
        for seed in SEEDS:
            arrays, answer, constants = closed(seed, 1.0, with_rates=False)
            rows, life = plant_rows(arrays, answer)
            normal = producers.share_working(1.0, 1.0)
            for row in rows.tolist():
                capacity = arrays.producers.capacity_runs[row]
                wear = capacity / life[row]
                worked = min(max(0.0, answer.new_last_runs[row]), capacity)
                wanted = capacity_toward_working(capacity, worked, normal, constants[K_WORKING_SHARE], constants[K_CHANGE])
                short = wanted - answer.new_capacity[row]
                expected = 0.0 if short <= 0.0 else min(short, constants[K_INERTIA] * wear, wear)
                self.assertAlmostEqual(answer.replacement_runs[row], expected, delta=1e-9 * max(1.0, capacity), msg=(seed, row))
                compared += 1
                rebuilt += expected > 0.0
        self.assertGreater(compared, 50)
        self.assertGreater(rebuilt, 5)          # the random economies reach both branches
        self.assertLess(rebuilt, compared)

    def test_with_no_weight_on_the_runs_worked_the_close_is_the_search_sets(self):
        for seed in SEEDS:
            _arrays, weighted_off, _constants = closed(seed, 0.0)
            setup, record, view, ledger, area_map = economy_of(seed, producer_count=60)
            arrays = YearArrays.build(setup, record, area_map, view)
            with mock.patch.object(AskAlternatives, "multiple", band_above_cost):
                search = close_producers(arrays, close_pack.pack(setup, record, view, ledger, arrays), None)
            np.testing.assert_array_equal(weighted_off.replacement_runs, search.replacement_runs)
            np.testing.assert_array_equal(weighted_off.expansion_runs, search.expansion_runs)
            np.testing.assert_array_equal(weighted_off.new_capacity, search.new_capacity)


if __name__ == "__main__":
    unittest.main()
