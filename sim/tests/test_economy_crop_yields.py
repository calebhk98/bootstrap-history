"""Complaint 537 and the externality door: the year's yield of a land-bound producer is the pooled weather times the
soil, climate and water of its tile for a recipe that crops, the weather alone for pasture and forest, and a harm factor
on its tile scales it further (`economy_port_sites.crop_yields` and `harmed_yields`). Called on a built economy, with no
game. The tile figures a setup carries are `test_economy_tiles_from_map` and `test_economy_port_cropland_yields`."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.economy.setup import recipe_tile_key
from sim.engine import economy_port_sites

WEATHER = 0.8


def producer(recipe_id, tile):
    return SimpleNamespace(recipe_id=recipe_id, tile=tile)


def economy():
    """Two farms on tiles of different soil, a farm on a tile with no site figure, a pasture and a mine."""
    setup = SimpleNamespace(
        yield_factor_by_recipe_tile={recipe_tile_key("wheat", "good"): 1.4, recipe_tile_key("wheat", "poor"): 0.6},
        land_per_run={"wheat": 2.0, "pasture": 5.0, "mine": 0.0}, countries=lambda: ["home"])
    producers = {"farm_good": producer("wheat", "good"), "farm_poor": producer("wheat", "poor"),
                 "farm_unsited": producer("wheat", "elsewhere"), "herd": producer("pasture", "good"),
                 "pit": producer("mine", "good")}
    return SimpleNamespace(setup=setup, record=SimpleNamespace(producers=producers))


class CropYieldsTests(unittest.TestCase):
    def setUp(self):
        self.yields = economy_port_sites.crop_yields(economy(), WEATHER)

    def test_a_crop_producer_yields_its_tiles_factor_times_the_weather(self):
        self.assertAlmostEqual(self.yields["farm_good"], WEATHER * 1.4)
        self.assertAlmostEqual(self.yields["farm_poor"], WEATHER * 0.6)

    def test_the_same_run_gives_more_on_the_better_tile(self):
        self.assertGreater(self.yields["farm_good"], self.yields["farm_poor"])

    def test_a_crop_on_a_tile_without_a_site_figure_follows_the_weather_alone(self):
        self.assertAlmostEqual(self.yields["farm_unsited"], WEATHER)

    def test_pasture_follows_the_weather_alone_even_on_a_tile_that_crops(self):
        self.assertAlmostEqual(self.yields["herd"], WEATHER)

    def test_a_producer_that_takes_no_land_has_no_yield_factor(self):
        self.assertNotIn("pit", self.yields)

    def test_no_weather_argument_is_a_normal_year(self):
        self.assertAlmostEqual(economy_port_sites.crop_yields(economy())["farm_good"], 1.4)


class TileWeatherTests(unittest.TestCase):
    """Complaint 537: a producer takes the weather of its own tile when the year has one, the pooled weather otherwise."""
    def setUp(self):
        self.yields = economy_port_sites.crop_yields(economy(), WEATHER, {"good": 1.1, "poor": 0.5})

    def test_a_crop_producer_takes_its_own_tiles_weather_times_its_tiles_factor(self):
        self.assertAlmostEqual(self.yields["farm_good"], 1.1 * 1.4)
        self.assertAlmostEqual(self.yields["farm_poor"], 0.5 * 0.6)

    def test_pasture_on_a_tile_takes_that_tiles_weather_too(self):
        self.assertAlmostEqual(self.yields["herd"], 1.1)

    def test_a_tile_without_a_weather_cell_takes_the_pooled_weather(self):
        self.assertAlmostEqual(self.yields["farm_unsited"], WEATHER)

    def test_two_tiles_with_one_soil_differ_only_by_their_weather(self):
        both = economy_port_sites.crop_yields(economy(), WEATHER, {"good": 0.7, "poor": 1.2})
        self.assertAlmostEqual(both["farm_good"] / 1.4, 0.7)
        self.assertAlmostEqual(both["farm_poor"] / 0.6, 1.2)


class HarmedYieldsTests(unittest.TestCase):
    def setUp(self):
        self.economy = economy()
        self.yields = economy_port_sites.crop_yields(self.economy, WEATHER)

    def harmed(self, harm_by_tile):
        return economy_port_sites.harmed_yields(self.yields, harm_by_tile, self.economy.record.producers)

    def test_a_harm_factor_scales_the_land_producers_of_that_tile_only(self):
        after = self.harmed({"good": 0.5})
        self.assertAlmostEqual(after["farm_good"], self.yields["farm_good"] * 0.5)
        self.assertAlmostEqual(after["herd"], self.yields["herd"] * 0.5)
        self.assertAlmostEqual(after["farm_poor"], self.yields["farm_poor"])

    def test_with_no_harm_the_yields_come_back_unchanged(self):
        self.assertIs(self.harmed({}), self.yields)

    def test_a_tile_no_provider_names_is_unharmed(self):
        self.assertEqual(self.harmed({"somewhere else": 0.1}), self.yields)


if __name__ == "__main__":
    unittest.main()
