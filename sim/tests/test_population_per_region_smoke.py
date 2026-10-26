"""SMOKE (Complaint 603): the Rome game keeps people by region (a tile the nation holds), each fed what its own households ate:
the nation is the sum of its regions, removing one tile's food lowers that tile's nutrition and raises its mortality and
no other tile's, and the economy is handed the regions' people. The rules on built populations are in
test_population_per_region_rule."""
import copy
import dataclasses
import unittest

from sim.demography.api import StepPopulation
from sim.tests.harness import unopened_sim as opened_game
from sim.tests.test_population_per_region_rule import _accounts


class TheGameTracksRegionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = opened_game(civ="rome_100ad")
        cls.start_world = copy.deepcopy(cls.game.state.modules["demography"])
        people = cls.game.labour.settlement_tiles()
        cls.tiles = sorted(tile for tile in people if people[tile] > 0.0)

    def _year(self, eaten_over_need_by_tile):
        game = self.game
        world = game.state.modules["demography"]
        for field in dataclasses.fields(world):
            setattr(world, field.name, copy.deepcopy(getattr(self.start_world, field.name)))
        game.record_food_eaten(type("Outcome", (), {"accounts": _accounts(eaten_over_need_by_tile)})())
        game.send(StepPopulation(game.state.scenario.year))
        return dict(game.view("regional_flows")())

    def test_the_nation_is_the_sum_of_its_regions_and_each_region_is_stored(self):
        self._year({tile: 1.0 for tile in self.tiles})
        stored = self.game.view("regional_people")()
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
