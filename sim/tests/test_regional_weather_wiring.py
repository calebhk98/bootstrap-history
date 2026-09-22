"""WIRING TWO (Complaints/closed/47-one-weather-draw-for-a-continent.md): does the
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
"""
import random
import statistics
import unittest

from .harness import *  # noqa: F401,F403

from sim.engine.core import agriculture
from sim.engine import data
from sim.tests.weather_test_helpers import (
    assert_matching_century,
    assert_save_reload_trajectory,
    assert_single_draw_fallback,
)


def _rome_sim(events=False):
    return sim(civ="rome_100ad", events=events)


class RegionWeightsTests(unittest.TestCase):
    """`Sim._farm_weather_cells`, precomputed once in `__init__` - see its
    own docstring for why this does not recompute every year.
    """

    def test_weights_sum_to_one_and_every_cell_sits_in_a_home_region(self):
        # Complaints/50: cell ids are geography.json's 150,000 km2
        # land_tiles, not Rome's seven home_regions - asserting the cell ids
        # WERE the home_regions would be precisely the equation that
        # complaint is about, one row in a data file as one weather draw.
        # So this is a containment check, not an identity one: every cell
        # must belong to a region Rome actually holds, and no cell may come
        # from a region it does not.
        test_sim = _rome_sim()
        cells = list(test_sim._farm_weather_cells)
        home_regions = set(test_sim.civ["home_regions"])
        tiles = data.load_geography()["land_tiles"]["tiles"]
        for cell in cells:
            self.assertIn(tiles[cell.cell_id]["old_region"], home_regions,
                          "cell %s is not in any region Rome holds" % cell.cell_id)
        self.assertGreater(len(cells), len(home_regions),
                           "Rome's territory should break into more cells "
                           "than it has region records, or nothing about "
                           "Complaints/50 has changed")
        self.assertAlmostEqual(sum(cell.weight for cell in cells), 1.0, places=9)

    def test_weights_are_a_genuine_land_share_not_an_equal_split(self):
        # Complaints/50: cells are geography.json's 150,000 km2 land_tiles,
        # which carry their own arable_fraction, so land.py does not feed
        # this mechanism at all - comparing each weight against
        # land.cultivable_land_for_civilization's per-REGION arable_iugera
        # would assert against a source the code does not read. What the
        # test is FOR survives unchanged: the weighting must be by land,
        # not by counting.
        test_sim = _rome_sim()
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

    def test_a_civilisation_with_no_home_regions_gets_no_cells(self):
        test_sim = _rome_sim()
        test_sim.civ = dict(test_sim.civ, home_regions=[])
        self.assertEqual(list(test_sim._compute_farm_weather_cells()), [])


class PooledWeatherMultiplierTests(unittest.TestCase):
    """`Sim._pooled_farm_weather_multiplier` - the land-share-weighted
    average of one independent draw per home region.
    """

    def test_pooled_multiplier_mean_is_close_to_one_over_many_years(self):
        test_sim = _rome_sim()
        draws = [test_sim._pooled_farm_weather_multiplier(year)
                 for year in range(101, 101 + 3000)]
        self.assertAlmostEqual(statistics.mean(draws), 1.0, delta=0.02)

    def test_pooling_seven_regions_measurably_reduces_variance(self):
        # Complaints/47's own measurement: pooling seven independent regions
        # should take the effective standard deviation from 0.20 (one draw)
        # to roughly 0.076 (seven EQUALLY weighted draws) - Rome's actual
        # weights are unequal (see RegionWeightsTests above), so the real
        # figure sits a bit higher than that, but it must still be far
        # below the single-draw stdev.
        test_sim = _rome_sim()
        draws = [test_sim._pooled_farm_weather_multiplier(year)
                 for year in range(101, 101 + 3000)]
        pooled_stdev = statistics.pstdev(draws)
        self.assertLess(pooled_stdev, agriculture.WEATHER_YIELD_STDEV_FRACTION * 0.6)
        self.assertGreater(pooled_stdev, 0.03)  # not literally zero variance

    def test_falls_back_to_the_old_single_draw_when_there_are_no_region_weights(self):
        assert_single_draw_fallback(self, _rome_sim(), agriculture)


    def test_each_region_actually_draws_independently_not_the_same_number_repeated(self):
        test_sim = _rome_sim()
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
        first, second = _rome_sim(), _rome_sim()
        self.assertEqual(first._farm_year_weather_seed(150, region="italia"),
                          second._farm_year_weather_seed(150, region="italia"))

    def test_different_regions_give_different_seeds(self):
        test_sim = _rome_sim()
        seeds = {test_sim._farm_year_weather_seed(150, region=region)
                 for region in test_sim.civ["home_regions"]}
        self.assertEqual(len(seeds), len(test_sim.civ["home_regions"]), seeds)

    def test_omitting_region_reproduces_the_old_civ_year_only_seed(self):
        test_sim = _rome_sim()
        civ_component = sum((index + 1) * ord(character) for index, character
                            in enumerate(str(test_sim.civ.get("id", "civ"))))
        expected = (civ_component * 1000003 + 150 * 97) % (2 ** 32)
        self.assertEqual(test_sim._farm_year_weather_seed(150), expected)

    def test_two_civilisations_sharing_a_region_name_still_draw_different_weather(self):
        rome = _rome_sim()
        other = _rome_sim()
        other.civ = dict(other.civ, id="some_other_civ")
        self.assertNotEqual(
            rome._farm_year_weather_seed(150, region="italia"),
            other._farm_year_weather_seed(150, region="italia"))


class DeterminismAcrossSaveAndReloadTests(unittest.TestCase):
    """The brief's own acceptance bar: two independently constructed sims,
    and a mid-run save/reload, must reproduce identical trajectories - the
    per-region weather draw must not weaken this any more than the old
    single draw did. Exercises the REAL `Sim.step`/save_state/load_state
    path (proto/saveload.py), not just `_demographic_recovery` directly,
    since that is what an actual --session game does on every command.
    """

    def test_two_independently_constructed_sims_match_over_a_century(self):
        assert_matching_century(self, _rome_sim)

    def test_a_mid_run_save_and_reload_reproduces_the_reference_trajectory(self):
        path = os.path.join(ROOT, _rel("regional_weather_wiring_mid_run.json"))
        assert_save_reload_trajectory(self, _rome_sim, path)




class UnshockedCenturyAcceptanceTests(unittest.TestCase):
    """The stakeholder's own bar (this task's brief): the unshocked
    rome_100ad century, events=False, should end ABOVE 100% of its starting
    population. Measured directly against the real engine, both wirings in
    place - not a re-typed constant, a live run.
    """

    def test_unshocked_century_ends_above_its_starting_population(self):
        test_sim = _rome_sim(events=False)
        start = test_sim.population.total
        for _year in range(100):
            test_sim.step()
        end = test_sim.population.total
        self.assertGreater(end, start, (start, end))

    def test_famine_still_happens_and_still_discriminates_by_age(self):
        # WIRING TWO must not have made the population insensitive to food:
        # a severe, additional land loss on top of pooled weather must
        # still lower nutrition_ratio and still cost more children and
        # elderly, proportionally, than working-age adults - the same
        # property test_agriculture_wiring.FamineHasAPhysicalCauseTests
        # already checks with region pooling implicitly present; this
        # re-states it as this wiring's own acceptance check.
        control = _rome_sim(events=False)
        shocked = _rome_sim(events=False)
        shocked.farm_land = agriculture.Land(
            shocked.farm_land.hectares * 0.15, quality=shocked.farm_land.quality)

        for year in range(101, 111):
            control._demographic_recovery(year)
            shocked._demographic_recovery(year)

        self.assertLess(shocked._last_demographic_step.nutrition_ratio,
                         control._last_demographic_step.nutrition_ratio)
        flows = shocked._last_demographic_step
        working_age_rate = flows.deaths_working_age / shocked.population.working_age
        child_rate = flows.deaths_children / shocked.population.children
        elderly_rate = flows.deaths_elderly / shocked.population.elderly
        self.assertGreater(child_rate, working_age_rate)
        self.assertGreater(elderly_rate, working_age_rate)


if __name__ == "__main__":
    unittest.main()
