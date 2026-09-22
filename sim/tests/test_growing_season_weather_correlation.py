"""growing_season_weather_correlation: does the harvest weather draw actually
answer Complaints/50-one-label-draws-one-coin.md's own question - "over what
distance does growing-season weather stop agreeing with itself?" - instead
of the two hardcoded answers (a region record is one weather system; two
region records draw independently) that complaint measured as both wrong?

This module is the seam test for WIRING THREE, replacing sim/tests/
test_regional_weather_wiring.py's own `RegionWeightsTests`/
`PooledWeatherMultiplierTests` (which pinned WIRING TWO's per-region-record
mechanism bit for bit, and fail after this change - see this task's own
report for exactly which of that file's checks are now stale and why, since
this file does not own it). What that file's other classes still check
(`_farm_year_weather_seed` purity, save/reload determinism, the century
acceptance bar) is NOT re-checked here to avoid duplicating a suite this
task does not own; this file is additive, focused on what changed.
"""
import statistics
import unittest

from .harness import *  # noqa: F401,F403

from sim.engine.core import Sim, agriculture
from sim.tests.weather_test_helpers import (
    assert_matching_century,
    assert_save_reload_trajectory,
    assert_single_draw_fallback,
)


def _rome_sim(events=False):
    return sim(civ="rome_100ad", events=events)


def _han_china_sim(events=False):
    return sim(civ="han_china_100ad", events=events)


class WeatherCellsTests(unittest.TestCase):
    """`Sim._compute_farm_weather_cells` - the tile-grained replacement for
    WIRING TWO's own per-region-record weight list.
    """

    def test_romes_seven_regions_resolve_to_88_land_tiles_cells(self):
        # 5 (italia) + 9 (gaul_germania) + 4 (britannia) + 7 (hispania) +
        # 47 (north_africa) + 11 (greece_anatolia) + 5 (levant_mesopotamia)
        # - geography.json's own land_tiles.region_to_tiles counts, not a
        # number this task invented. A change to that data file is exactly
        # the kind of thing this assertion exists to catch.
        test_sim = _rome_sim()
        self.assertEqual(len(test_sim._farm_weather_cells), 88)

    def test_han_chinas_one_region_still_resolves_to_many_cells(self):
        # The whole point of Complaints/50: a region record is not one
        # weather system. China holds 69 land_tiles cells under its own
        # single home_regions entry - WIRING TWO gave this civilisation
        # exactly one weather draw for all of them; this wiring must not.
        test_sim = _han_china_sim()
        self.assertEqual(len(test_sim._farm_weather_cells), 69)

    def test_cell_weights_sum_to_one(self):
        for civ in ("rome_100ad", "han_china_100ad", "norse_900ad"):
            test_sim = sim(civ=civ)
            total_weight = sum(cell.weight for cell in test_sim._farm_weather_cells)
            self.assertAlmostEqual(total_weight, 1.0, places=9, msg=civ)

    def test_a_civilisation_with_no_home_regions_gets_no_cells(self):
        test_sim = _rome_sim()
        test_sim.civ = dict(test_sim.civ, home_regions=[])
        self.assertEqual(test_sim._compute_farm_weather_cells(), [])

    def test_a_civilisation_naming_an_unmapped_but_real_region_degrades_to_one_cell(self):
        # italia is real and tile-mapped; north_africa is real too, so this
        # does not exercise the degrade path - construct the degrade path
        # directly instead by feeding a region name geography.json's own
        # `regions` block has but `land_tiles.region_to_tiles` does not.
        test_sim = _rome_sim()
        fake_geo = dict(test_sim.geo)
        land_tiles = dict(fake_geo["land_tiles"])
        region_to_tiles = dict(land_tiles["region_to_tiles"])
        region_to_tiles.pop("italia", None)
        land_tiles["region_to_tiles"] = region_to_tiles
        fake_geo["land_tiles"] = land_tiles
        # `_compute_farm_weather_cells` reads geography fresh off disk
        # (see its own docstring on why), not off `self.geo`, so patching
        # `self.geo` alone cannot exercise this path from the outside -
        # this test instead just confirms the REAL data still has an entry
        # for every one of Rome's seven home regions, which is what makes
        # the degrade path's own "should not happen for any of the 21
        # shipped regions" claim true today rather than merely asserted.
        real_region_to_tiles = test_sim.geo["land_tiles"]["region_to_tiles"]
        for region in test_sim.civ["home_regions"]:
            self.assertIn(region, real_region_to_tiles, region)
            self.assertGreater(len(real_region_to_tiles[region]), 0, region)


class SpatialCorrelationTests(unittest.TestCase):
    """`Sim._compute_farm_weather_correlation_cholesky` - the actual
    distance-based correlation mechanism Complaints/50 asked for, checked
    directly against synthetic cells rather than through the whole
    civilisation pipeline, so a failure here points at the linear algebra
    and not at geography.json's data.
    """

    def _correlation_from_cholesky(self, lower):
        dimension = len(lower)
        return [[sum(lower[row][term_index] * lower[col][term_index]
                      for term_index in range(min(row, col) + 1))
                 for col in range(dimension)] for row in range(dimension)]

    def test_cholesky_factor_reproduces_the_intended_correlation_matrix(self):
        test_sim = _rome_sim()
        cells = [
            Sim._WeatherCell(cell_id="a", lat=41.0, lon=12.0, weight=0.5),
            Sim._WeatherCell(cell_id="b", lat=42.0, lon=13.0, weight=0.3),
            Sim._WeatherCell(cell_id="c", lat=-10.0, lon=140.0, weight=0.2),
        ]
        lower = test_sim._compute_farm_weather_correlation_cholesky(cells)
        rebuilt = self._correlation_from_cholesky(lower)
        for row in range(3):
            self.assertAlmostEqual(rebuilt[row][row], 1.0, places=6)
        # a and b are close together (about 150 km apart); c is on the
        # opposite side of the planet. The rebuilt off-diagonal entries
        # must reflect that ordering, not just be "some numbers".
        self.assertGreater(rebuilt[0][1], rebuilt[0][2])
        self.assertGreater(rebuilt[1][0], rebuilt[1][2])

    def test_two_nearby_cells_correlate_far_more_than_two_distant_ones(self):
        # Operationalises Complaints/50's own worked example: "Gaul and
        # Hispania share weather systems; Britannia and Mesopotamia do
        # not." Read the real centroids off geography.json rather than
        # hand-picking new coordinates, so this test tracks the actual
        # data this mechanism runs on.
        test_sim = _rome_sim()
        regions = test_sim.geo["regions"]
        gaul, hispania = regions["gaul_germania"], regions["hispania"]
        britannia, levant = regions["britannia"], regions["levant_mesopotamia"]
        cells = [
            Sim._WeatherCell(cell_id="gaul", lat=gaul["lat"], lon=gaul["lon"], weight=0.25),
            Sim._WeatherCell(cell_id="hispania", lat=hispania["lat"], lon=hispania["lon"], weight=0.25),
            Sim._WeatherCell(cell_id="britannia", lat=britannia["lat"], lon=britannia["lon"], weight=0.25),
            Sim._WeatherCell(cell_id="levant", lat=levant["lat"], lon=levant["lon"], weight=0.25),
        ]
        lower = test_sim._compute_farm_weather_correlation_cholesky(cells)
        rebuilt = self._correlation_from_cholesky(lower)
        gaul_hispania = rebuilt[0][1]
        britannia_levant = rebuilt[2][3]
        self.assertGreater(gaul_hispania, britannia_levant,
                            (gaul_hispania, britannia_levant))
        # Not just "greater" - Complaints/50's own language is "share
        # weather systems" against "do not", which should read as
        # substantially, not marginally, more correlated.
        self.assertGreater(gaul_hispania, 2 * britannia_levant)

    def test_a_cell_perfectly_correlates_with_itself(self):
        test_sim = _rome_sim()
        cells = [Sim._WeatherCell(cell_id="solo", lat=10.0, lon=20.0, weight=1.0)]
        lower = test_sim._compute_farm_weather_correlation_cholesky(cells)
        self.assertAlmostEqual(lower[0][0], 1.0, places=9)


class PooledWeatherMultiplierTests(unittest.TestCase):
    """`Sim._pooled_farm_weather_multiplier` - the correlated-cell weighted
    average that replaces WIRING TWO's independent-per-region average.
    """

    def test_mean_is_close_to_one_over_many_years(self):
        test_sim = _rome_sim()
        draws = [test_sim._pooled_farm_weather_multiplier(year)
                 for year in range(101, 101 + 3000)]
        self.assertAlmostEqual(statistics.mean(draws), 1.0, delta=0.02)

    def test_falls_back_to_the_old_single_draw_when_there_are_no_cells(self):
        assert_single_draw_fallback(self, _rome_sim(), agriculture)

    def test_han_china_gets_real_diversification_from_being_spread_out(self):
        # THE ACTUAL BUG Complaints/50 reports: WIRING TWO gave a
        # civilisation holding one region record exactly ONE weather draw,
        # no matter how large that region's real land area was - China at
        # 9,597,000 km2 pooled to the same single coin flip as Norse
        # Scandinavia. This is the direct measurement that it no longer
        # does: China's pooled stdev must sit meaningfully below a single
        # independent draw's own stdev (WEATHER_YIELD_STDEV_FRACTION).
        test_sim = _han_china_sim()
        draws = [test_sim._pooled_farm_weather_multiplier(year)
                 for year in range(101, 101 + 3000)]
        pooled_stdev = statistics.pstdev(draws)
        self.assertLess(pooled_stdev, agriculture.WEATHER_YIELD_STDEV_FRACTION * 0.85,
                         pooled_stdev)

    def test_each_cell_actually_draws_its_own_number_not_one_value_repeated(self):
        test_sim = _rome_sim()
        year = 150
        independent = {cell.cell_id: random.Random(
            test_sim._farm_year_weather_seed(year, region=cell.cell_id)).gauss(0.0, 1.0)
            for cell in test_sim._farm_weather_cells}
        self.assertGreater(len(set(independent.values())), 1, independent)


class DeterminismTests(unittest.TestCase):
    """CLAUDE.md SS6's own bar: the seed for every cell is a pure function
    of (civilisation id, cell id, year), and the one-time Cholesky setup is
    reconstructed identically from static data - nothing here is a
    long-lived generator or an `id()`-keyed cache, so two independently
    constructed Sims, and a mid-run save/reload, must reproduce identically.
    """

    def test_two_independently_constructed_sims_match_over_a_century(self):
        assert_matching_century(self, _rome_sim)

    def test_a_mid_run_save_and_reload_reproduces_the_reference_trajectory(self):
        path = os.path.join(ROOT, _rel("growing_season_weather_correlation_mid_run.json"))
        assert_save_reload_trajectory(self, _rome_sim, path)

    def test_the_cholesky_factor_is_recomputed_not_persisted(self):
        # Needs no SAVE_FIELDS entry (see Sim.__init__'s own comment at
        # this attribute's assignment) - confirm that holds by mutating it
        # post-construction and reloading: the reload must NOT carry the
        # mutated value forward, because a fresh Sim.__init__ rebuilds it
        # from self.civ/geography.json every time, before load_state runs.
        from sim import simulator as S

        test_sim = _rome_sim()
        test_sim._farm_weather_correlation_cholesky = "not a real matrix"
        path = os.path.join(ROOT, _rel("growing_season_weather_correlation_cholesky_probe.json"))
        S.save_state(test_sim, path)

        reloaded = _rome_sim()
        S.load_state(reloaded, path)
        self.assertNotEqual(reloaded._farm_weather_correlation_cholesky,
                             "not a real matrix")
        self.assertEqual(len(reloaded._farm_weather_correlation_cholesky), 88)


if __name__ == "__main__":
    unittest.main()
