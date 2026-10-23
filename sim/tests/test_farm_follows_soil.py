"""Complaint 543: the national farm model reads the soil nitrogen stock each year, so continuous cropping lowers the
national harvest, and a rotation's legumes raise it through the stock alone (the rotation has no yield multiplier). The
rules are called on the held tiles of a civilisation and the map; the farm following the tiles is test_refresh_farm_territory_rule."""
QUICK_TOPIC = True

import unittest

from sim.engine.data import load_civ
from sim.geography import food_society, soil_nitrogen
from sim.geography.api import open_map, tiles_held
from sim.world import agriculture, agriculture_tile, land
from sim.world.farming_technique import DEFAULT_TECHNIQUE

YEARS = 30
REFERENCE_CROPPED_SHARE = 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding


class FarmFollowsSoil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.civ = load_civ("rome_100ad")
        cls.world_map = open_map()
        cls.held = tiles_held(cls.civ, cls.world_map)

    def harvest_weight(self, cropped_share, stock):
        """Cropped hectares times yield factor over the held ground under this stock."""
        factors = soil_nitrogen.yield_factors(stock, self.held, cropped_share, REFERENCE_CROPPED_SHARE, 0.0)
        sites = food_society.crop_sites(self.civ, self.world_map, cropped_share, factors)
        return sum(factor * hectares for factor, hectares in land.territory_cropland(sites).ladder)

    def years_under(self, rotation):
        """(harvest weight before, after, mean stock after) over YEARS of cropping under the rotation."""
        technique = DEFAULT_TECHNIQUE._replace(rotation=rotation)
        kg_per_hectare = agriculture_tile.crop_technique(technique).kg_per_cropped_hectare
        share = 1.0 - rotation.fallow_share_of_holding
        stock = {}
        before = self.harvest_weight(share, stock)
        for _year in range(YEARS):
            sites = soil_nitrogen.unworn_sites(self.civ, self.world_map, share)
            soil_nitrogen.step_year(stock, sites, kg_per_hectare, rotation.legume_share_of_holding,
                                    REFERENCE_CROPPED_SHARE, 0.0)
        return before, self.harvest_weight(share, stock), sum(stock.values()) / len(stock)

    def test_continuous_cropping_lowers_the_national_harvest(self):
        continuous = agriculture.DEFAULT_ROTATION._replace(name="continuous", fallow_share_of_holding=0.0)
        before, after, stock_after = self.years_under(continuous)
        self.assertLess(stock_after, 1.0)
        self.assertLess(after, before)

    def test_the_three_field_edge_is_the_stocks(self):
        without_legumes = agriculture.THREE_FIELD._replace(name="three_field_no_legumes", legume_share_of_holding=0.0)
        _before, harvest_with, stock_with = self.years_under(agriculture.THREE_FIELD)
        _before, harvest_without, stock_without = self.years_under(without_legumes)
        self.assertGreater(stock_with, stock_without)
        self.assertGreater(harvest_with, harvest_without)

    def test_the_ceiling_follows_a_change_of_rotation(self):
        def ceiling(rotation):
            sites = food_society.crop_sites(self.civ, self.world_map, 1.0 - rotation.fallow_share_of_holding, {})
            return land.territory_cropland(sites).cropped_hectares
        self.assertGreater(ceiling(agriculture.THREE_FIELD), ceiling(agriculture.DEFAULT_ROTATION))


if __name__ == "__main__":
    unittest.main()
