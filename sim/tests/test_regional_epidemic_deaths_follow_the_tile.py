"""Complaint 677: a region's epidemic deaths are the deaths that happened on its tile, not its share of the nation's.

Rule test of `regional_population.step_regions`; the inputs are built here."""
import unittest

from sim.world import regional_population
from sim.world.demography import Population

QUICK_TOPIC = True

BANDS = regional_population.BANDS


def _regions():
    return {"hit": Population.stationary(100000.0), "spared": Population.stationary(100000.0)}


def _fed(regions):
    return {tile: regional_population.kcal_per_day_fed(region, 1.0) for tile, region in regions.items()}


def _step(regions, national_deaths, deaths_by_tile):
    return regional_population.step_regions(
        regions, _fed(regions), 0.0, national_deaths, None, {}, {}, epidemic_deaths_by_tile=deaths_by_tile)


class EpidemicDeathsFollowTheTileTests(unittest.TestCase):
    def test_deaths_fall_on_the_tile_where_they_happened(self):
        national = {"children": 0.0, "working_age": 2000.0, "elderly": 0.0}
        flows_by_tile = _step(_regions(), national, {"hit": dict(national)})
        baseline = _step(_regions(), {}, None)
        extra_hit = flows_by_tile["hit"].deaths - baseline["hit"].deaths
        extra_spared = flows_by_tile["spared"].deaths - baseline["spared"].deaths
        self.assertAlmostEqual(extra_hit, 2000.0, delta=1.0)
        self.assertAlmostEqual(extra_spared, 0.0, delta=1.0)

    def test_without_deaths_by_tile_the_nations_are_shared_by_band_share(self):
        national = {"children": 0.0, "working_age": 2000.0, "elderly": 0.0}
        flows = _step(_regions(), national, None)
        baseline = _step(_regions(), {}, None)
        for tile in ("hit", "spared"):
            self.assertAlmostEqual(flows[tile].deaths - baseline[tile].deaths, 1000.0, delta=1.0)

    def test_deaths_the_tiles_do_not_account_for_are_shared_by_band_share(self):
        national = {"children": 0.0, "working_age": 3000.0, "elderly": 0.0}
        by_tile = {"hit": {"children": 0.0, "working_age": 1000.0, "elderly": 0.0}}
        flows = _step(_regions(), national, by_tile)
        baseline = _step(_regions(), {}, None)
        self.assertAlmostEqual(flows["hit"].deaths - baseline["hit"].deaths, 2000.0, delta=1.0)
        self.assertAlmostEqual(flows["spared"].deaths - baseline["spared"].deaths, 1000.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
