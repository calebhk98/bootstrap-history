"""Per-tile food potential: finite on every tile, plausible by climate, and driven by map data only."""
import math
import os
import statistics
import unittest

from sim.geography import map_source, parameters, tile_layers
from sim.geography.food_capacity import food_potential, food_potential_all

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geography_fixtures")
DRAGON_MOD = "food_overlay_q7x2"
DRAGON = DRAGON_MOD + ":dragon"
FORAGER_SOURCES = ("hunting", "foraging", "marine_fishing", "freshwater_fishing")
_cache = {}


def earth():
    if "earth" not in _cache:
        world_map = map_source.load_map()
        _cache["earth"] = (world_map, food_potential_all(world_map))
    return _cache["earth"]


def per_km2(world_map, tile_id, kcal):
    kcal_per_person = world_map.catalogue("parameters")["food_kcal_per_person_year"]["value"]
    return kcal / world_map.tiles[tile_id]["land_area_km2"] / kcal_per_person


def class_median(world_map, results, prefix, sources):
    values = [sum(per_km2(world_map, tile_id, results[tile_id]["kcal_per_year"].get(source, 0.0)) for source in sources)
              for tile_id, tile in world_map.tiles.items() if tile["koppen_class"].startswith(prefix)]
    return statistics.median(values)


class FoodTests(unittest.TestCase):
    def test_parameters_are_complete(self):
        self.assertEqual(parameters.invalid_entries(earth()[0]), [])

    def test_every_tile_is_finite_and_non_negative(self):
        _world_map, results = earth()
        for tile_id, result in results.items():
            for kcal in list(result["kcal_per_year"].values()) + [result["people_supported"]]:
                self.assertTrue(math.isfinite(kcal) and kcal >= 0.0, tile_id)

    def test_foragers_alone_stay_in_a_hunter_gatherer_band(self):
        world_map, results = earth()
        for prefix in ("A", "C", "D"):
            self.assertTrue(0.01 <= class_median(world_map, results, prefix, FORAGER_SOURCES) <= 1.0, prefix)
        self.assertLess(class_median(world_map, results, "BW", FORAGER_SOURCES), 0.1)
        self.assertLess(class_median(world_map, results, "EF", FORAGER_SOURCES), 0.01)

    def test_pastoral_is_higher_on_steppe_than_desert(self):
        world_map, results = earth()
        self.assertGreater(class_median(world_map, results, "BS", ("pastoral",)),
                           2 * class_median(world_map, results, "BWh", ("pastoral",)))

    def test_crops_dominate_fertile_temperate_tiles_and_desert_is_far_poorer(self):
        world_map, results = earth()
        for prefix in ("Cs", "Cf"):
            tiles = [t for t, tile in world_map.tiles.items() if tile["koppen_class"].startswith(prefix)
                     and tile["arable_fraction"] >= 0.2 and tile_layers.number(world_map, t, "mean_temperature_c", 0) >= 8
                     and tile_layers.number(world_map, t, "annual_precipitation_mm", 0) >= 400]
            self.assertTrue(tiles)
            for tile_id in tiles:
                kcal = results[tile_id]["kcal_per_year"]
                self.assertEqual(max(kcal, key=kcal.get), "crops", tile_id)
        everything = ("crops", "pastoral") + FORAGER_SOURCES
        self.assertLess(10 * class_median(world_map, results, "BWh", everything),
                        class_median(world_map, results, "Cs", everything))

    def test_a_large_river_feeds_a_desert(self):
        world_map, results = earth()
        desert = [t for t, tile in world_map.tiles.items() if tile["koppen_class"] == "BWh"
                  and tile_layers.number(world_map, t, "annual_precipitation_mm", 0) < 100]
        watered = [t for t in desert if tile_layers.number(world_map, t, "river_km_navigable", 0) > 300]
        dry = [t for t in desert if tile_layers.number(world_map, t, "river_km_all", 0) == 0
               and not world_map.tiles[t]["coastal"]]
        self.assertTrue(watered and dry)
        density = lambda t: results[t]["people_supported"] / world_map.tiles[t]["land_area_km2"]
        self.assertGreater(min(density(t) for t in watered), 10 * max(density(t) for t in dry))

    def test_only_coastal_tiles_get_marine_fish(self):
        world_map, results = earth()
        coastal = [t for t, tile in world_map.tiles.items() if tile["coastal"]]
        self.assertTrue(any(results[t]["kcal_per_year"].get("marine_fishing", 0) > 0 for t in coastal))
        for tile_id, tile in world_map.tiles.items():
            if not tile["coastal"]:
                self.assertEqual(results[tile_id]["kcal_per_year"].get("marine_fishing", 0), 0, tile_id)

    def test_technique_factors_scale_one_source(self):
        world_map, results = earth()
        tile_id = next(t for t, r in results.items()
                       if r["kcal_per_year"].get("crops", 0) > 0 and r["kcal_per_year"].get("pastoral", 0) > 0)
        boosted = food_potential(world_map, tile_id, {"crops": 2.0})
        self.assertAlmostEqual(boosted["kcal_per_year"]["crops"], 2 * results[tile_id]["kcal_per_year"]["crops"])
        self.assertAlmostEqual(boosted["kcal_per_year"]["pastoral"], results[tile_id]["kcal_per_year"]["pastoral"])

    def test_class_fallbacks_answer_a_map_without_measured_layers(self):
        world_map, results = earth()
        bare = map_source.WorldMap(world_map.map_id, world_map.tiles, {}, world_map.catalogues, world_map.folders)
        bare_results = food_potential_all(bare)
        self.assertEqual(set(bare_results), set(results))
        self.assertTrue(all(math.isfinite(r["total_kcal_per_year"]) for r in bare_results.values()))
        self.assertGreater(statistics.median(r["total_kcal_per_year"] for r in bare_results.values()), 0)


class ModAnimalTests(unittest.TestCase):
    def test_a_mod_game_animal_is_hunted_where_its_envelope_fits_and_nowhere_else(self):
        base_map, base = earth()
        overlay_map = map_source.load_map(((DRAGON_MOD, os.path.join(FIXTURES, "food_mod_overlay")),))
        modded = food_potential_all(overlay_map)
        fitted = 0
        for tile_id in base_map.tiles:
            before = base[tile_id]["kcal_per_year"].get("hunting", 0.0)
            after = modded[tile_id]["kcal_per_year"].get("hunting", 0.0)
            if DRAGON in modded[tile_id]["species"]["hunted"]:
                fitted += 1
                self.assertGreater(after, before, tile_id)
            else:
                self.assertEqual(after, before, tile_id)
        self.assertGreater(fitted, 0)
        self.assertLess(fitted, len(base_map.tiles) // 2)


if __name__ == "__main__":
    unittest.main()
