"""Complaint 543: the soil nitrogen stock of a civilisation's held cropland is saved with the game, a year of cropping
draws the held cropland down, and a worn tile feeds fewer people. The rules are called on the held tiles of a civilisation
and the map (no game); the same through a whole game is test_soil_nitrogen_whole_game."""

QUICK_TOPIC = True

import unittest

from sim.engine.data import load_civ
from sim.engine.state import EconomyState, deserialize_state, serialize_state
from sim.geography import food_society, soil_nitrogen
from sim.geography.api import crop_site, open_map, tiles_held
from sim.world import agriculture_tile
from sim.world.farming_technique import DEFAULT_TECHNIQUE

REFERENCE_CROPPED_SHARE = 0.5
KG_PER_HECTARE = 1000.0


class HeldLandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.civ = load_civ("rome_100ad")
        cls.world_map = open_map()
        cls.held = tiles_held(cls.civ, cls.world_map)

    def test_the_stock_round_trips_through_a_save(self):
        tile_id = sorted(self.world_map.tiles)[0]
        economy = EconomyState()
        economy.soil_nitrogen = {tile_id: 0.6}
        self.assertEqual(deserialize_state(serialize_state(economy), EconomyState).soil_nitrogen, {tile_id: 0.6})

    def test_a_year_of_cropping_draws_the_held_cropland_down(self):
        stock = {}
        sites = soil_nitrogen.unworn_sites(self.civ, self.world_map, REFERENCE_CROPPED_SHARE)
        soil_nitrogen.step_year(stock, sites, KG_PER_HECTARE, 0.0, REFERENCE_CROPPED_SHARE, 0.0)
        cropped = [tile for tile in self.held if crop_site(tile, REFERENCE_CROPPED_SHARE, self.world_map).yield_factor > 0.0]
        self.assertTrue(cropped)
        self.assertTrue(all(0.0 < stock[tile] < 1.0 for tile in cropped))

    def test_a_tile_that_is_not_held_is_not_drawn_down(self):
        stock = {}
        sites = soil_nitrogen.unworn_sites(self.civ, self.world_map, REFERENCE_CROPPED_SHARE)
        soil_nitrogen.step_year(stock, sites, KG_PER_HECTARE, 0.0, REFERENCE_CROPPED_SHARE, 0.0)
        self.assertTrue(set(stock) <= set(self.held))

    def test_a_worn_tile_feeds_fewer_people(self):
        technique = agriculture_tile.crop_technique(DEFAULT_TECHNIQUE)
        native = food_society.food_kcal_by_source(self.civ, self.world_map, {}, technique, {})
        worn_factors = {tile: 0.3 for tile in self.held}
        worn = food_society.food_kcal_by_source(self.civ, self.world_map, {}, technique, worn_factors)
        self.assertLess(sum(worn.values()), sum(native.values()))


if __name__ == "__main__":
    unittest.main()
