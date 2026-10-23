"""SCENARIO: the economy's carriage costs on the base map's real tiles equal geography's route costs (Complaint 408). The
rules on synthetic grids are in test_economy_tile_costs.py."""
import json
import os
import unittest

from sim.economy import tile_costs
from sim.geography import api as geography_api
from sim.tests.test_economy_tile_costs import CROPPED_SHARE, REAL_HANDLING, REAL_RATES, ROOT


def civ_tile_ids(geography, civ_name):
    """The tiles the civ holds."""
    with open(os.path.join(ROOT, "data", "civilizations", civ_name + ".json"), encoding="utf-8") as handle:
        civ = json.load(handle)
    return geography_api.tiles_held(civ)


class GeographyIsTheSourceTests(unittest.TestCase):
    """The economy's carriage costs are geography's route costs on the same tiles (Complaint 408)."""

    @classmethod
    def setUpClass(cls):
        cls.geography = geography_api.load_geography()
        cls.tile_ids = civ_tile_ids(cls.geography, "rome_100ad")
        cls.tiles = tile_costs.tiles_from_map(geography_api.open_map(), cls.tile_ids, CROPPED_SHARE)

    def test_a_river_link_geography_knows_is_cheaper_by_boat_in_the_economy(self):
        inside = set(self.tile_ids)
        rivers = [(a, b) for a, b, _mode, _km in geography_api.freight_links(["river_boat"])
                  if a in inside and b in inside]
        self.assertTrue(rivers, "the civilisation's tiles hold a navigable river link")
        downstream = [(source, target) for a, b in rivers for source, target in ((a, b), (b, a))
                      if geography_api.route([source], [target], ["river_boat"]) is not None]
        self.assertTrue(downstream, "a boat can run along one of them")
        first, second = downstream[0]
        with_boats = tile_costs.carriage_table(self.tiles, {"cart": 5.0, "river_boat": 0.01})
        without = tile_costs.carriage_table(self.tiles, {"cart": 5.0})
        self.assertLess(with_boats.cost_per_tonne(first, second), without.cost_per_tonne(first, second))

    def test_costs_equal_geographys_route_cost_for_the_same_rates(self):
        table = tile_costs.carriage_table(self.tiles, REAL_RATES, REAL_HANDLING)
        first, last = self.tile_ids[0], self.tile_ids[-1]
        found = geography_api.route([first], [last], sorted(REAL_RATES), mode_costs=REAL_RATES,
                                    handling_costs=REAL_HANDLING)
        self.assertIsNotNone(found)
        self.assertAlmostEqual(table.cost_per_tonne(first, last), found["cost_per_tonne"], places=6)

    def test_no_tile_of_the_civilisation_is_cut_off(self):
        table = tile_costs.carriage_table(self.tiles, REAL_RATES, REAL_HANDLING)
        reached = table.costs_from(self.tile_ids[0])
        self.assertEqual(set(reached), set(self.tile_ids))

    def test_tiles_from_geography_reads_fields(self):
        tile_id = sorted(self.geography["land_tiles"]["tiles"])[0]
        tiles = tile_costs.tiles_from_map(geography_api.open_map(), [tile_id], CROPPED_SHARE)
        record = self.geography["land_tiles"]["tiles"][tile_id]
        self.assertEqual(tiles[tile_id].latitude, record["lat"])
        site = geography_api.crop_site(tile_id, CROPPED_SHARE)
        self.assertEqual(tiles[tile_id].fertility, site.yield_factor)
        self.assertAlmostEqual(tiles[tile_id].cropland_hectares, site.cropped_hectares)
        self.assertEqual(tiles[tile_id].borders, tuple(record["borders"]))


if __name__ == "__main__":
    unittest.main()
