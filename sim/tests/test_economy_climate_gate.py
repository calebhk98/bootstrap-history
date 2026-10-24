"""A crop runs only on tiles of the climates its data names."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import recipes, sites
from sim.tests import economy_fixture as fixture


class ClimateGateTests(unittest.TestCase):
    def test_the_production_entry_names_the_climates(self):
        recipe = recipes.recipe_from_entry("cocoa", {"outputs": {"cocoa": 1.0}, "labour_hours": {"labourer": 1.0},
                                                     "grown_in_climate_classes": ["Af", "Am"]})
        self.assertEqual(recipe.climate_classes, ("Af", "Am"))

    def test_a_tile_of_another_climate_is_not_allowed_and_an_unknown_one_is(self):
        recipe = dataclasses.replace(fixture.recipes()[fixture.FARM], climate_classes=("Cfb",))
        tiles = fixture.tiles()
        self.assertTrue(sites.climate_allows(recipe, tiles[fixture.TOWN]))
        self.assertFalse(sites.climate_allows(recipe, dataclasses.replace(tiles[fixture.TOWN], climate_class="BWh")))
        self.assertTrue(sites.climate_allows(recipe, dataclasses.replace(tiles[fixture.TOWN], climate_class="Cfb")))

    def test_grain_is_placed_only_on_tiles_of_its_climate(self):
        tiles = {tile: dataclasses.replace(spec, climate_class="Cfb" if tile == fixture.FARMS else "BWh")
                 for tile, spec in fixture.tiles().items()}
        recipe = dataclasses.replace(fixture.recipes()[fixture.FARM], climate_classes=("Cfb",), site_bound=True)
        self.assertEqual(sites.suited_tiles(recipe, tiles, sorted(tiles)), (fixture.FARMS,))


if __name__ == "__main__":
    unittest.main()
