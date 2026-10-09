"""WIRING TWO (Complaints/closed/46-one-weather-draw-for-a-continent.md): does the
engine actually draw one weather multiplier PER HOME REGION and pool them
weighted by cultivable land share, or does the whole territory still share
a single draw?

This module is the seam test between sim/engine/core.py and sim/world/land.
py (read-only - see core.py's own comment on that import): sim/world/
agriculture.py's own test suite proves `draw_weather_multiplier` and
`Storage.step`'s new `weather_multiplier` override correct in isolation;
this checks that core.py actually builds land-share weights from Rome's
seven home_regions, draws one independent multiplier per region, and pools
them - and that the century-level acceptance target this wiring exists for
is actually met.

Weather is drawn per home region and pooled by cultivable-land share; the seed is a pure function of (civ, region, year).
"""

import os
import statistics
import tempfile
import unittest

from .harness import *  # noqa: F401,F403

from sim.engine.core import agriculture
from sim.engine import data
from sim.geography import api as geography_api
from sim.tests.weather_test_helpers import assert_matching_century, assert_save_reload_trajectory

# Long enough for weather to shape population and stock, short enough to stay cheap; the
# engine's own yearly market keeps each year fast and weather does not depend on the market.
DETERMINISM_YEARS = 20


def _market_free_rome():
    return sim(civ="rome_100ad", events=False, agent_economy=False)



def _rome_sim(events=False):
    return sim(civ="rome_100ad", events=events)


# Read-only checks share one game; checks that change the civilisation restore it.
SHARED_ROME = _rome_sim()
HOME_REGIONS = geography_api.regions_of_tiles(geography_api.tiles_held(SHARED_ROME.civ))


class RegionWeightsTests(unittest.TestCase):
    """`Sim._farm_weather_cells`, precomputed once in `__init__` - see its
    own docstring for why this does not recompute every year.
    """

    def test_weights_sum_to_one_and_every_cell_sits_in_a_home_region(self):
        # Complaints/49: cell ids are geography.json's 150,000 km2
        # land_tiles, not Rome's seven home_regions - asserting the cell ids
        # WERE the home_regions would be precisely the equation that
        # complaint is about, one row in a data file as one weather draw.
        # So this is a containment check, not an identity one: every cell
        # must belong to a region Rome actually holds, and no cell may come
        # from a region it does not.
        test_sim = SHARED_ROME
        cells = list(test_sim._farm_weather_cells)
        home_regions = set(geography_api.regions_of_tiles(geography_api.tiles_held(test_sim.civ)))
        tiles = data.load_geography()["land_tiles"]["tiles"]
        for cell in cells:
            self.assertIn(tiles[cell.cell_id]["old_region"], home_regions,
                          "cell %s is not in any region Rome holds" % cell.cell_id)
        self.assertGreater(len(cells), len(home_regions),
                           "Rome's territory should break into more cells "
                           "than it has region records, or nothing about "
                           "Complaints/49 has changed")
        self.assertAlmostEqual(sum(cell.weight for cell in cells), 1.0, places=9)

    def test_weights_are_a_genuine_land_share_not_an_equal_split(self):
        # Complaints/49: cells are geography.json's 150,000 km2 land_tiles,
        # which carry their own arable_fraction, so land.py does not feed
        # this mechanism at all - comparing each weight against
        # land.cultivable_land_for_civilization's per-REGION arable_hectares
        # would assert against a source the code does not read. What the
        # test is FOR survives unchanged: the weighting must be by land,
        # not by counting.
        test_sim = SHARED_ROME
        weights = [cell.weight for cell in test_sim._farm_weather_cells]
        self.assertGreater(len(weights), 7,
                           "Rome's territory should break into many more "
                           "cells than its seven region records")
        self.assertAlmostEqual(sum(weights), 1.0, places=9)
        # An equal split would make every weight identical. A real
        # land-share weighting does not - a desert cell and a Nile cell
        # are not the same size of harvest.
        self.assertGreater(max(weights), min(weights),
                           "every cell carries the same weight, which means "
                           "the weighting is a count and not an area")

class PooledWeatherMultiplierTests(unittest.TestCase):
    """`Sim._pooled_farm_weather_multiplier` - the land-share-weighted
    average of one independent draw per home region.
    """

    def test_pooling_seven_regions_measurably_reduces_variance(self):
        # Complaints/46's own measurement: pooling seven independent regions
        # should take the effective standard deviation from 0.20 (one draw)
        # to roughly 0.076 (seven EQUALLY weighted draws) - Rome's actual
        # weights are unequal (see RegionWeightsTests above), so the real
        # figure sits a bit higher than that, but it must still be far
        # below the single-draw stdev.
        test_sim = SHARED_ROME
        draws = [test_sim._pooled_farm_weather_multiplier(year)
                 for year in range(101, 101 + 1000)]
        pooled_stdev = statistics.pstdev(draws)
        self.assertLess(pooled_stdev, agriculture.WEATHER_YIELD_STDEV_FRACTION * 0.6)
        self.assertGreater(pooled_stdev, 0.03)  # not literally zero variance

    def test_each_region_actually_draws_independently_not_the_same_number_repeated(self):
        test_sim = SHARED_ROME
        year = 150
        draws = {cell.cell_id: agriculture.draw_weather_multiplier(
                    random.Random(
                        test_sim._farm_year_weather_seed(year, region=cell.cell_id)),
                    agriculture.DEFAULT_SOIL.weather_stdev_fraction)
                 for cell in test_sim._farm_weather_cells}
        # Dozens of independent draws landing on the exact same float by
        # chance is vanishingly unlikely - if this ever fires, the cell id
        # is not actually reaching the seed.
        self.assertGreater(len(set(draws.values())), 1, draws)


class WeatherSeedPurityTests(unittest.TestCase):
    """`_farm_year_weather_seed(yr, region=...)` must stay a pure function
    of (civilisation id, region, year) - no long-lived generator, so a
    --session save/reload cannot lose or repeat a draw. See the method's
    own docstring for why this matters more than it looks like it should.
    """

    def test_same_inputs_always_give_the_same_seed(self):
        first, second = SHARED_ROME, _rome_sim()
        self.assertEqual(first._farm_year_weather_seed(150, region="italia"),
                          second._farm_year_weather_seed(150, region="italia"))

    def test_different_regions_give_different_seeds(self):
        test_sim = SHARED_ROME
        seeds = {test_sim._farm_year_weather_seed(150, region=region)
                 for region in HOME_REGIONS}
        self.assertEqual(len(seeds), len(HOME_REGIONS), seeds)

    def test_omitting_region_mixes_in_no_region_ingredient(self):
        # Without a region the seed is a function of civilisation id, year and the game's
        # weather salt only (the salt is the game's own dice, so each game has its own weather).
        test_sim = SHARED_ROME
        seed = test_sim._farm_year_weather_seed(150)
        salt = test_sim.state.scenario.weather_salt
        self.assertTrue(salt)
        civ_component = sum((index + 1) * ord(character) for index, character
                            in enumerate(str(test_sim.civ.get("id", "civ"))))
        expected = (civ_component * 1000003 + 150 * 97 + salt * 104729) % (2 ** 32)
        self.assertEqual(seed, expected)

    def test_two_civilisations_sharing_a_region_name_still_draw_different_weather(self):
        rome_seed = SHARED_ROME._farm_year_weather_seed(150, region="italia")
        original_civ = SHARED_ROME.civ
        SHARED_ROME.civ = dict(original_civ, id="some_other_civ")
        try:
            other_seed = SHARED_ROME._farm_year_weather_seed(150, region="italia")
        finally:
            SHARED_ROME.civ = original_civ
        self.assertNotEqual(rome_seed, other_seed)


class DeterminismAcrossSaveAndReloadTests(unittest.TestCase):
    """Weather is a pure function of (civ, region, year, salt): two games match, and a save/reload mid-run loses no draw."""

    def test_two_games_stay_identical_year_for_year(self):
        assert_matching_century(self, _market_free_rome, years=DETERMINISM_YEARS)

    def test_a_mid_run_save_and_reload_follows_the_same_trajectory(self):
        with tempfile.TemporaryDirectory() as folder:
            assert_save_reload_trajectory(
                self, _market_free_rome, os.path.join(folder, "weather_trajectory.json"),
                years=DETERMINISM_YEARS)

    def test_pooled_multiplier_averages_close_to_one(self):
        draws = [SHARED_ROME._pooled_farm_weather_multiplier(year)
                 for year in range(101, 101 + 400)]
        self.assertAlmostEqual(statistics.fmean(draws), 1.0, delta=0.02)


class UnshockedCenturyAcceptanceTests(unittest.TestCase):
    """The stakeholder's own bar (this task's brief): the unshocked
    rome_100ad century, events=False, should end ABOVE 100% of its starting
    population. Measured directly against the real engine, both wirings in
    place - not a re-typed constant, a live run.
    """

    def test_unshocked_century_ends_above_its_starting_population(self):
        test_sim = _rome_sim(events=False)
        start = test_sim.population.total
        for year in range(101, 201):
            test_sim._demographic_recovery(year)
        end = test_sim.population.total
        self.assertGreater(end, start, (start, end))


if __name__ == "__main__":
    unittest.main()
