"""A crop runs only on tiles of the climates its data names."""
import dataclasses
import unittest

from sim.economy import recipes, sites
from sim.economy.economy import Economy
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

    def test_grain_is_grown_only_where_its_climate_is(self):
        tiles = {tile: dataclasses.replace(spec, climate_class="Cfb" if tile == fixture.FARMS else "BWh")
                 for tile, spec in fixture.tiles().items()}
        the_recipes = fixture.recipes()
        the_recipes[fixture.FARM] = dataclasses.replace(the_recipes[fixture.FARM], climate_classes=("Cfb",),
                                                        site_bound=True)
        setup = fixture.small_setup(tiles=tiles, recipes=the_recipes)
        economy, _outcomes = fixture.run(setup, years=6)
        grain_tiles = {producer.tile for producer in economy.record.producers.values()
                       if producer.recipe_id == fixture.FARM}
        self.assertEqual(grain_tiles, {fixture.FARMS})
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())


if __name__ == "__main__":
    unittest.main()
