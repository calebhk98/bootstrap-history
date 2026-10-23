"""Complaint 603: people are tracked by region (a tile the nation holds), each fed what its own households ate.

The nation's population is the sum of the regions. Two regions of unequal food: the poor one loses more people to
hunger and sends migrants to the fed one. Built populations and accounts; no game. The same rules in a played game are
in test_population_per_region."""
import unittest

from sim.economy.year_accounts import CohortAccount, YearAccounts, _tiles
from sim.labour.api import moves_between_regions
from sim.world import regional_population
from sim.world.demography import Population

QUICK_TOPIC = True


class TwoRegionsOfUnequalFoodTests(unittest.TestCase):
    def setUp(self):
        self.regions = {"delta": Population.stationary(100000.0), "frontier": Population.stationary(100000.0)}
        self.eaten_over_need = {"delta": 1.2, "frontier": 0.7}
        self.borders = {"delta": ["frontier"], "frontier": ["delta"]}

    def _year(self):
        kcal = {tile: regional_population.kcal_per_day_fed(region, self.eaten_over_need[tile])
                for tile, region in self.regions.items()}
        leaving, arriving = moves_between_regions(
            self.regions, self.eaten_over_need, self.borders, lambda origin, destination: 50.0)
        flows = regional_population.step_regions(self.regions, kcal, 1.0, {}, None, leaving, arriving)
        return flows, leaving, arriving

    def test_the_poor_region_loses_people_to_hunger_and_sends_migrants(self):
        flows, leaving, arriving = self._year()
        poor, rich = flows["frontier"], flows["delta"]
        self.assertGreater(poor.deaths / poor.start_total, rich.deaths / rich.start_total)
        self.assertGreater(leaving["frontier"], leaving.get("delta", 0.0))
        self.assertGreater(arriving["delta"], arriving.get("frontier", 0.0))

    def test_the_national_figure_is_the_sum_of_the_regions(self):
        flows, _leaving, _arriving = self._year()
        total = regional_population.national_flows(flows, 1.0)
        self.assertAlmostEqual(sum(region.total for region in self.regions.values()), total.end_total, places=6)
        self.assertAlmostEqual(total.start_total + total.births - total.deaths, total.end_total, places=6)

    def test_migrants_are_neither_made_nor_lost(self):
        flows, leaving, arriving = self._year()
        self.assertAlmostEqual(sum(leaving.values()), sum(arriving.values()), places=9)
        total = regional_population.national_flows(flows, 1.0)
        self.assertAlmostEqual(total.immigration, total.emigration, places=9)

    def test_regions_are_kept_to_the_nation_after_it_changes_outside_the_step(self):
        national = Population(1000.0, 3000.0, 500.0)
        regions = {"a": Population(100.0, 100.0, 100.0), "b": Population(300.0, 300.0, 300.0)}
        regional_population.keep_to_nation(regions, national, ["a", "b", "c"], {"a": 0.2, "b": 0.5, "c": 0.3})
        for band in regional_population.BANDS:
            self.assertAlmostEqual(sum(getattr(region, band) for region in regions.values()), getattr(national, band))
        self.assertGreater(regions["c"].total, 0.0)


def _accounts(eaten_over_need_by_tile):
    cohorts = [CohortAccount(cohort="cohort:" + tile, tile=tile, income_class=0, people=1000.0, need_per_head=100.0,
                             eaten_per_head=100.0 * eaten, bought_per_head=100.0 * eaten, own_plot_per_head=0.0,
                             real_income_per_head=1.0) for tile, eaten in eaten_over_need_by_tile.items()]
    return YearAccounts(year=1, cohorts=cohorts, tiles=_tiles(cohorts))


if __name__ == "__main__":
    unittest.main()
