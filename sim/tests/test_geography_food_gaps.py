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


class SharedShelfTests(unittest.TestCase):
    def test_neighbouring_coastal_tiles_split_one_shelf(self):
        alone = mini_map({"a": (COASTAL, {}, [])})
        trio = mini_map({name: (COASTAL, {}, [other for other in "abc" if other != name]) for name in "abc"})
        whole = kcal(alone, "a", "marine_fishing")
        self.assertGreater(whole, 0.0)
        shared = sum(kcal(trio, name, "marine_fishing") for name in "abc")
        self.assertAlmostEqual(shared, whole, delta=0.01 * whole)

    def test_a_coastal_tile_with_no_coastal_neighbour_keeps_its_whole_shelf(self):
        alone = mini_map({"a": (COASTAL, {}, [])})
        inland = mini_map({"a": (COASTAL, {}, ["b"]), "b": ("afghanistan_01", {}, ["a"])})
        self.assertAlmostEqual(kcal(inland, "a", "marine_fishing"), kcal(alone, "a", "marine_fishing"))

    def test_real_coastal_tiles_no_longer_out_fish_their_fields(self):
        for tile_id in ("united_kingdom_01", "china_45", "south_korea_01", "netherlands_01"):
            result = api.food_potential(tile_id)["kcal_per_year"]
            self.assertLess(result.get("marine_fishing", 0.0), 0.15 * result["crops"], tile_id)


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


if __name__ == "__main__":
    unittest.main()
