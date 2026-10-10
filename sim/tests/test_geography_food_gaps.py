"""Food potential gaps of Complaint 411: shared shelf, slope, growing season, forest and wild-grazer competition.

Tiles are copies of real map tiles with chosen layer values, so every case runs without a game.
"""

QUICK_TOPIC = True

import unittest

from sim.geography import api, food_season, map_source
from sim.geography.food_capacity import food_potential

_cache = {}


def earth():
    if "earth" not in _cache:
        _cache["earth"] = map_source.load_map()
    return _cache["earth"]


def mini_map(specs, drop_wild=False):
    """A map of copies of real tiles. specs: {new_id: (real_tile_id, {layer: value}, [bordering new ids])}."""
    real = earth()
    tiles, layers = {}, {name: dict(layer, values={}) for name, layer in real.layers.items()}
    for new_id, (real_id, overrides, borders) in specs.items():
        tiles[new_id] = dict(real.tiles[real_id], id=new_id, borders=list(borders))
        for name, layer in real.layers.items():
            found = layer["values"].get(real_id)
            if found is not None:
                layers[name]["values"][new_id] = found
        for name, found in overrides.items():
            layers.setdefault(name, {"values": {}})["values"][new_id] = found
    catalogues = dict(real.catalogues)
    if drop_wild:
        catalogues["resources"] = {row_id: row for row_id, row in real.catalogue("resources").items()
                                   if row.get("mechanism") != "wild_population"}
    return map_source.WorldMap("mini", tiles, layers, catalogues, real.folders, real.properties)


def kcal(world_map, tile_id, source):
    return food_potential(world_map, tile_id)["kcal_per_year"].get(source, 0.0)


COASTAL = "united_kingdom_01"
FARMLAND = "france_05"
COLD = "canada_30"
STEPPE = "canada_10"


class PartitionedShelfTests(unittest.TestCase):
    def test_a_tiles_fishing_does_not_depend_on_its_neighbours(self):
        alone = mini_map({"a": (COASTAL, {}, [])})
        crowded = mini_map({name: (COASTAL, {}, [other for other in "abc" if other != name]) for name in "abc"})
        whole = kcal(alone, "a", "marine_fishing")
        self.assertGreater(whole, 0.0)
        self.assertAlmostEqual(kcal(crowded, "a", "marine_fishing"), whole)

    def test_the_shelf_layer_adds_up_to_no_more_than_the_physical_shelf(self):
        # Continental shelves (seabed shallower than 200 m) cover on the order of thirty million km2 worldwide.
        total = sum(earth().layers["shelf_area_km2"]["values"].values())
        self.assertLess(total, 30.0e6)
        self.assertGreater(total, 15.0e6)

    def test_real_coastal_tiles_no_longer_out_fish_their_fields(self):
        for tile_id in ("united_kingdom_01", "china_45", "south_korea_01", "netherlands_01"):
            result = api.food_potential(tile_id)["kcal_per_year"]
            self.assertLess(result.get("marine_fishing", 0.0), 0.15 * result["crops"], tile_id)

    def test_nearest_land_partition_splits_a_strait_down_the_middle(self):
        try:
            import shapely
            from sim.geography.layer_build.layers_shelf import nearest_land_shares
        except ImportError:
            self.skipTest("the layer build needs shapely")
        left = shapely.box(0, 0, 10000, 100000)
        right = shapely.box(30000, 0, 40000, 100000)
        sea = shapely.box(10000, 0, 30000, 100000)
        shares = nearest_land_shares(sea, {"left": left, "right": right})
        self.assertAlmostEqual(shares["left"], shares["right"], delta=0.02 * sea.area)
        self.assertAlmostEqual(shares["left"] + shares["right"], sea.area, delta=0.01 * sea.area)
        far = nearest_land_shares(sea, {"left": left, "right": shapely.box(50000, 0, 60000, 100000)})
        self.assertAlmostEqual(far["left"], sea.area, delta=0.01 * sea.area)
        self.assertLess(far["right"], 0.01 * sea.area)


class SlopeTests(unittest.TestCase):
    def test_rugged_land_is_cropped_and_grazed_less(self):
        flat = mini_map({"a": (FARMLAND, {"ruggedness_index": 5.0}, [])})
        steep = mini_map({"a": (FARMLAND, {"ruggedness_index": 450.0}, [])})
        self.assertGreater(kcal(flat, "a", "crops"), 1.5 * kcal(steep, "a", "crops"))
        self.assertGreater(kcal(flat, "a", "pastoral"), kcal(steep, "a", "pastoral"))

    def test_gentle_land_is_not_limited(self):
        gentle = mini_map({"a": (FARMLAND, {"ruggedness_index": 0.0}, [])})
        flat = mini_map({"a": (FARMLAND, {"ruggedness_index": 5.0}, [])})
        self.assertAlmostEqual(kcal(gentle, "a", "crops"), kcal(flat, "a", "crops"))


class GrowingSeasonTests(unittest.TestCase):
    def season(self, mean, warmest, coldest):
        layers = {"mean_temperature_c": mean, "warmest_month_temperature_c": warmest,
                  "coldest_month_temperature_c": coldest}
        return food_season.growing_season_fraction(mini_map({"a": (FARMLAND, layers, [])}), "a")

    def test_warm_year_round_has_a_full_season_and_a_polar_year_none(self):
        self.assertEqual(self.season(26.0, 28.0, 24.0), 1.0)
        self.assertEqual(self.season(-15.0, 1.0, -30.0), 0.0)

    def test_colder_winters_shorten_the_season(self):
        mild = self.season(10.0, 18.0, 2.0)
        harsh = self.season(3.0, 16.0, -20.0)
        self.assertTrue(0.0 < harsh < mild < 1.0)

    def test_a_short_season_cuts_herding_below_the_same_rain_in_a_long_one(self):
        cold = mini_map({"a": (COLD, {"annual_precipitation_mm": 500.0, "mean_temperature_c": -3.0,
                                      "coldest_month_temperature_c": -24.0,
                                      "warmest_month_temperature_c": 14.0}, [])})
        warm = mini_map({"a": (COLD, {"annual_precipitation_mm": 500.0, "mean_temperature_c": 12.0,
                                      "coldest_month_temperature_c": 2.0,
                                      "warmest_month_temperature_c": 22.0}, [])})
        self.assertLess(kcal(cold, "a", "pastoral"), 0.4 * kcal(warm, "a", "pastoral"))

    def test_subarctic_herding_is_well_under_a_person_per_square_km(self):
        world_map = earth()
        values = sorted(api.food_potential(tile_id)["kcal_per_year"].get("pastoral", 0.0)
                        / world_map.tiles[tile_id]["land_area_km2"]
                        for tile_id, tile in world_map.tiles.items() if tile["koppen_class"] == "Dfc")
        kcal_per_person = world_map.catalogue("parameters")["food_kcal_per_person_year"]["value"]
        self.assertLess(values[len(values) // 2] / kcal_per_person, 0.4)


class CompetitionTests(unittest.TestCase):
    def test_forest_takes_cropland(self):
        open_land = mini_map({"a": (FARMLAND, {"forest_fraction": 0.0}, [])})
        wooded = mini_map({"a": (FARMLAND, {"forest_fraction": 0.95}, [])})
        self.assertLess(kcal(wooded, "a", "crops"), 0.9 * kcal(open_land, "a", "crops"))

    def test_wild_grazers_eat_the_grass_herds_would_have(self):
        with_game = mini_map({"a": (STEPPE, {}, [])})
        without_game = mini_map({"a": (STEPPE, {}, [])}, drop_wild=True)
        self.assertGreater(kcal(without_game, "a", "pastoral"), 1.05 * kcal(with_game, "a", "pastoral"))
        self.assertGreater(kcal(with_game, "a", "pastoral"), 0.0)


class RainforestTests(unittest.TestCase):
    def crops(self, rain, forest, arable=0.2):
        layers = {"annual_precipitation_mm": rain, "forest_fraction": forest, "arable_fraction": arable,
                  "ruggedness_index": 0.0, "river_km_navigable": 0.0, "river_km_all": 0.0}
        return kcal(mini_map({"a": (FARMLAND, layers, [])}), "a", "crops")

    def test_humid_tropical_rain_is_not_waterlogging(self):
        self.assertAlmostEqual(self.crops(2400.0, 0.0), self.crops(1400.0, 0.0), delta=0.01 * self.crops(1400.0, 0.0))
        self.assertGreater(self.crops(4500.0, 0.0), 0.0)
        self.assertLess(self.crops(4500.0, 0.0), self.crops(2400.0, 0.0))

    def test_land_cleared_from_forest_is_cropped_in_a_long_fallow_rotation(self):
        open_land = self.crops(2400.0, 0.0)
        cleared = self.crops(2400.0, 0.95)
        self.assertLess(cleared, 0.6 * open_land)
        self.assertGreater(cleared, 0.2 * open_land)

    def test_rainforest_cropping_is_within_reach_of_savanna_cropping(self):
        world_map = earth()
        medians = {}
        for koppen in ("Af", "Aw"):
            values = sorted(api.food_potential(tile_id)["kcal_per_year"]["crops"] / tile["land_area_km2"]
                            for tile_id, tile in world_map.tiles.items() if tile["koppen_class"] == koppen)
            medians[koppen] = values[len(values) // 2]
        self.assertGreater(medians["Af"], 0.5 * medians["Aw"])


if __name__ == "__main__":
    unittest.main()
