"""Complaint 603: people are tracked by region (a tile the nation holds), each fed what its own households ate.

The nation's population is the sum of the regions. Two regions of unequal food: the poor one loses more people to
hunger and sends migrants to the fed one. Removing one tile's food lowers that tile's nutrition and raises its
mortality and leaves every other tile's as it was."""
import copy
import unittest

from sim.economy.year_accounts import CohortAccount, YearAccounts, _tiles
from sim.engine import regional_people
from sim.tests.harness import sim as opened_game
from sim.world import regional_population
from sim.world.demography import Population


class TwoRegionsOfUnequalFoodTests(unittest.TestCase):
    def setUp(self):
        self.regions = {"delta": Population.stationary(100000.0), "frontier": Population.stationary(100000.0)}
        self.eaten_over_need = {"delta": 1.2, "frontier": 0.7}
        self.borders = {"delta": ["frontier"], "frontier": ["delta"]}

    def _year(self):
        kcal = {tile: regional_population.kcal_per_day_fed(region, self.eaten_over_need[tile])
                for tile, region in self.regions.items()}
        leaving, arriving = regional_people.moves_between_regions(
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


class TheGameTracksRegionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = opened_game(civ="rome_100ad")
        cls.start_state = copy.deepcopy(cls.game.state.population)
        cls.start_population = copy.deepcopy(cls.game.population)
        people = cls.game.labour.settlement_tiles()
        cls.tiles = sorted(tile for tile in people if people[tile] > 0.0)

    def _year(self, eaten_over_need_by_tile):
        game = self.game
        game.state.population = copy.deepcopy(self.start_state)
        game.population = copy.deepcopy(self.start_population)
        game.record_food_eaten(type("Outcome", (), {"accounts": _accounts(eaten_over_need_by_tile)})())
        game._demographic_recovery(game.state.scenario.year)
        return dict(game._last_regional_step)

    def test_the_nation_is_the_sum_of_its_regions_and_each_region_is_stored(self):
        self._year({tile: 1.0 for tile in self.tiles})
        stored = self.game.state.population.regions
        self.assertEqual(sorted(stored), sorted(self.game.labour.settlement_tiles()))
        self.assertAlmostEqual(sum(sum(bands) for bands in stored.values()), self.game.population.total, delta=1.0)

    def test_removing_a_tiles_food_lowers_its_nutrition_and_raises_its_mortality_and_no_other_tiles(self):
        eaten = {tile: 1.0 for tile in self.tiles}
        fed = self._year(eaten)
        town = max(self.tiles, key=lambda tile: fed[tile].start_total)
        eaten[town] = 0.5
        cut = self._year(eaten)
        self.assertLess(cut[town].nutrition_ratio, fed[town].nutrition_ratio)
        self.assertGreater(cut[town].deaths / cut[town].start_total, fed[town].deaths / fed[town].start_total)
        for tile in self.tiles:
            if tile != town:
                self.assertEqual(cut[tile].nutrition_ratio, fed[tile].nutrition_ratio)
                self.assertAlmostEqual(cut[tile].deaths / cut[tile].start_total,
                                       fed[tile].deaths / fed[tile].start_total, places=12)

    def test_the_economy_is_handed_the_regions_people(self):
        eaten = {tile: 1.0 for tile in self.tiles}
        eaten[self.tiles[0]] = 0.5
        self._year(eaten)
        self.assertEqual(self.game.labour.settlement_tiles(), self.game.people_by_tile())
        self.assertAlmostEqual(sum(self.game.labour.settlement_tiles().values()), self.game.population.total, delta=1.0)


if __name__ == "__main__":
    unittest.main()
