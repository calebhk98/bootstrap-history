"""SCENARIO: Complaint 603, the urban share of an opened game comes from its regions.

The typed `urban_fraction` seeds the opening's split among the regions; afterwards only the food the towns can draw
bounds it. Every reader goes through `Sim.urban_fraction`."""
import json
import os
import unittest
from unittest import mock

from sim.tests.harness import unopened_sim
from sim.tests.urban_share_opening import BANDS_PATH
from sim.world import urban_share


def _bands():
    with open(BANDS_PATH, encoding="utf-8") as handle:
        return json.load(handle)["bands"]


class OpeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = unopened_sim("rome_100ad")

    def test_the_computed_share_at_the_opening_is_inside_the_civilisations_band(self):
        band = urban_share.band_for("rome_100ad", _bands())
        self.assertTrue(urban_share.within_band(self.game.urban_fraction(), band))

    def test_the_food_the_towns_can_carry_is_at_least_the_opening_share(self):
        people = self.game._people_for_urban_share()
        ceilings = self.game.urban_ceilings()
        carried = sum(min(ceilings[tile], people[tile]) for tile in people) / self.game.population.total
        self.assertGreaterEqual(carried, self.game.urban_fraction())

    def test_coastal_towns_can_feed_more_of_their_people_than_inland_ones(self):
        people = self.game._people_for_urban_share()
        ceilings = self.game.urban_ceilings()
        def fed_share(wanted):
            tiles = [tile for tile in people if bool(self.game.world_map.tiles[tile].get("coastal")) is wanted]
            return sum(min(ceilings[tile], people[tile]) for tile in tiles) / sum(people[tile] for tile in tiles)
        self.assertGreater(fed_share(True), fed_share(False))

    def test_the_typed_figure_is_read_once_at_the_opening_and_not_again(self):
        game = unopened_sim("rome_100ad")
        before = game.urban_fraction()
        game.civ["urban_fraction"] = 0.9
        self.assertAlmostEqual(game.urban_fraction(), before)

    def test_a_poorer_surplus_shrinks_the_towns(self):
        game = unopened_sim("rome_100ad")
        before = game.urban_fraction()
        real = type(game)._computed_urban_ceilings
        with mock.patch.object(type(game), "_computed_urban_ceilings",
                               lambda self, *args: {tile: 0.2 * people for tile, people in real(self, *args).items()}):
            game.__dict__.pop("_urban_ceilings_cache", None)
            after = game.urban_fraction()
        self.assertLess(after, before)

    def test_the_share_survives_a_save(self):
        game = unopened_sim("rome_100ad")
        game.urban_fraction()
        self.assertEqual(sorted(game.state.population.urban_share_of_people), sorted(game._people_for_urban_share()))


if __name__ == "__main__":
    unittest.main()
