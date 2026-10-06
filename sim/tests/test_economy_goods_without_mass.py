"""Goods whose unit is not a mass must not be carried as 1 kg never-spoiling goods."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import market_areas, tile_costs
from sim.economy.setup import goods_specs
from sim.economy.types import TileSpec
from sim.geography import transport

GOODS = ["ox", "mule", "hectare_land", "mechanical_mj", "stone_tons", "stone_blocks", "brick_1000",
         "timber_m3", "wheat_kg"]


def specs():
    return goods_specs({good: "" for good in GOODS}, {})


class GoodsWithoutMass(unittest.TestCase):
    def test_animals_weigh_their_live_weight(self):
        self.assertEqual(specs()["ox"].unit_mass_kg, transport.OX_BODY_MASS_KG)
        self.assertEqual(specs()["mule"].unit_mass_kg, transport.MULE_BODY_MASS_KG)

    def test_ground_and_energy_cannot_be_carried(self):
        for good in ("hectare_land", "mechanical_mj"):
            self.assertFalse(specs()[good].portable, good)
        self.assertTrue(specs()["wheat_kg"].portable)

    def test_tonne_unit_is_a_tonne(self):
        self.assertEqual(specs()["stone_tons"].unit_mass_kg, 1000.0)

    def test_heavy_building_goods_are_not_a_kilogram(self):
        for good in ("stone_blocks", "brick_1000", "timber_m3"):
            self.assertGreater(specs()[good].unit_mass_kg, 100.0, good)

    def test_immobile_good_has_no_market_area_beyond_its_tile(self):
        tiles = {name: TileSpec(name, 40.0, longitude, 1000.0, False, ("a", "b"), 0.5, 1.0)
                 for name, longitude in (("a", 0.0), ("b", 1.0))}
        table = tile_costs.carriage_table(tiles, {"cart": 1.0, "pack": 1.0}, world_map=tile_costs.world_map_of(tiles))
        spec = specs()["hectare_land"]
        self.assertEqual(market_areas.value_per_tonne(spec, 100.0), 0.0)
        areas = market_areas.partition(tiles, table, market_areas.value_per_tonne(spec, 100.0), {"a": 1, "b": 1})
        self.assertEqual(len(areas), 2)
        self.assertTrue(math.isinf(spec.unit_mass_kg))


if __name__ == "__main__":
    unittest.main()
