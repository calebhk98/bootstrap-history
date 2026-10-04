"""Resource endowment and prospecting: known plus hidden deposits, deterministic, size-biased, mod-extensible."""
import hashlib
import os
import statistics
import unittest

from sim.geography import (map_source, resources_biotic, resources_catalogue, resources_draws,
                           resources_endowment, resources_prospecting, resources_summary, tile_layers)
from sim.geography.distance import haversine_km

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geography_fixtures")
SMALL = os.path.join(FIXTURES, "resources_small")
OVERLAY = (("test_resources_m4n8", os.path.join(FIXTURES, "resources_overlay")),)
EARTH_DEPOSITS = (("test_resources_e5r1", os.path.join(FIXTURES, "resources_earth_deposits")),)
UNOBTAINIUM = "test_resources_m4n8:unobtainium"


def small_map(overlays=()):
    return map_source.load_map(overlays, SMALL)


def earth_map():
    return map_source.load_map(EARTH_DEPOSITS)


def with_resources(world_map, resources):
    catalogues = dict(world_map.catalogues, resources=resources)
    return map_source.WorldMap(world_map.map_id, world_map.tiles, world_map.layers, catalogues, world_map.folders)


class CatalogueTests(unittest.TestCase):
    def test_fixture_and_earth_definitions_validate(self):
        self.assertEqual(resources_catalogue.validate(small_map()), [])
        self.assertEqual(resources_catalogue.validate(small_map(OVERLAY)), [])
        self.assertEqual(resources_catalogue.validate(map_source.load_map()), [])
        self.assertEqual(resources_catalogue.validate(earth_map()), [])

    def test_unknown_mechanism_fails_naming_the_resource(self):
        broken = with_resources(small_map(), {"rock": {"id": "rock", "mechanism": "magic", "unit": "kg"}})
        with self.assertRaisesRegex(map_source.MapDataError, "rock.*magic"):
            resources_catalogue.resource_definitions(broken)

    def test_other_models_entries_are_left_alone(self):
        self.assertNotIn("goat", resources_catalogue.resource_definitions(small_map()))

    def test_known_deposits_convert_units_and_sit_in_the_nearest_tile(self):
        world_map = small_map()
        by_id = {deposit["id"]: deposit for deposit in resources_catalogue.known_deposits(world_map, "gold")}
        self.assertEqual(by_id["big_gold"]["tile_id"], "a1")
        self.assertAlmostEqual(by_id["big_gold"]["quantity"], 5e6)
        self.assertEqual(by_id["old_vein"]["tile_id"], "b2")
        self.assertAlmostEqual(by_id["old_vein"]["quantity"], 1000.0)


class EndowmentTests(unittest.TestCase):
    def test_known_deposits_are_counted_and_giants_cluster_near_them(self):
        world_map = small_map()
        near = resources_endowment.endowment(world_map, "a1", "gold")
        far = resources_endowment.endowment(world_map, "a3", "gold")
        self.assertAlmostEqual(near["known"], 5e6)
        self.assertEqual(far["known"], 0)
        giant = [deposit_type for deposit_type in resources_catalogue.resource(world_map, "gold")["deposit_types"]
                 if deposit_type["id"] == "giant"][0]
        giant_near = resources_endowment.clustering_multiplier(world_map, "a1", "gold", giant)
        giant_far = resources_endowment.clustering_multiplier(world_map, "a3", "gold", giant)
        self.assertGreater(giant_near, 20 * giant_far)

    def test_a_known_deposit_is_taken_out_of_its_types_expected_count(self):
        world_map = small_map()
        row = [row for row in resources_endowment.expected_counts(world_map, "b2", "gold")
               if row["deposit_type"] == "vein"][0]
        self.assertLess(row["expected_count"], 20 / 1e6 * 150000 * 10.0)

    def test_layer_weights_remove_a_resource_from_unsuited_climates(self):
        world_map = small_map()
        coal_desert = resources_endowment.endowment(world_map, "a2", "coal")
        coal_boreal = resources_endowment.endowment(world_map, "b2", "coal")
        self.assertEqual(coal_desert["expected_undiscovered_count"], 0.0)
        self.assertGreater(coal_boreal["expected_undiscovered_count"], 1.0)

    def test_endowment_of_a_mod_resource_needs_no_code(self):
        world_map = small_map(OVERLAY)
        found = resources_endowment.endowment(world_map, "a2", UNOBTAINIUM)
        self.assertAlmostEqual(found["known"], 50000.0)
        self.assertGreater(found["undiscovered_expected"], 0.0)
        self.assertEqual(resources_endowment.endowment(world_map, "b3", UNOBTAINIUM)["known"], 0)
        self.assertIn(UNOBTAINIUM, resources_summary.resources_at(world_map, "a2"))

    def test_resources_at_lists_biotic_and_mineral_entries(self):
        summary = resources_summary.resources_at(small_map(), "b1")
        self.assertIn("coal", summary)
        self.assertIn("timber", summary)
        self.assertNotIn("timber", resources_summary.resources_at(small_map(), "a2"))


class DrawTests(unittest.TestCase):
    def test_uniform_is_a_sha256_of_the_labels(self):
        digest = hashlib.sha256(b"a|7|b").digest()
        expected = (int.from_bytes(digest[:8], "big") + 0.5) / 2.0 ** 64
        self.assertEqual(resources_draws.uniform("a", 7, "b"), expected)

    def test_truncated_mean_matches_the_draws(self):
        draws = [resources_draws.truncated_lognormal(100.0, 1.2, 2.0, "t", index) for index in range(20000)]
        expected = resources_draws.truncated_lognormal_mean(100.0, 1.2, 2.0)
        self.assertAlmostEqual(statistics.fmean(draws) / expected, 1.0, delta=0.05)


class ProspectingTests(unittest.TestCase):
    def test_hidden_deposits_are_deterministic_and_seed_dependent(self):
        world_map = small_map()
        first = resources_prospecting.hidden_deposits(world_map, "b2", "coal", 7)
        self.assertEqual(first, resources_prospecting.hidden_deposits(world_map, "b2", "coal", 7))
        other = [len(resources_prospecting.hidden_deposits(world_map, "b2", "coal", seed)) for seed in range(20)]
        self.assertGreater(len(set(other)), 3)

    def test_mean_count_matches_the_expected_count(self):
        world_map = small_map()
        expected = resources_endowment.expected_counts(world_map, "b2", "coal")[0]["expected_count"]
        counts = [len(resources_prospecting.hidden_deposits(world_map, "b2", "coal", seed)) for seed in range(400)]
        self.assertAlmostEqual(statistics.fmean(counts) / expected, 1.0, delta=0.15)

    def test_deposits_lie_in_their_tile_with_plain_data(self):
        world_map = small_map()
        tile = world_map.tiles["b2"]
        for deposit in resources_prospecting.hidden_deposits(world_map, "b2", "coal", 3):
            self.assertLess(haversine_km(tile["lat"], tile["lon"], deposit["lat"], deposit["lon"]), 300)
            self.assertTrue(all(isinstance(value, (int, float, str, bool)) for value in deposit.values()))
            self.assertGreater(deposit["ore_tonnes"], 0)

    def test_more_effort_finds_a_superset(self):
        world_map = small_map()
        previous = set()
        sizes = []
        for effort in (0, 500, 3000, 20000, 1e9):
            found = {deposit["id"] for deposit in resources_prospecting.prospect(world_map, "b2", "coal", effort, 5)}
            self.assertTrue(previous <= found)
            self.assertEqual(found, {deposit["id"] for deposit in
                                     resources_prospecting.prospect(world_map, "b2", "coal", effort, 5)})
            previous = found
            sizes.append(len(found))
        self.assertEqual(sizes[0], 0)
        self.assertEqual(sizes[-1], len(resources_prospecting.hidden_deposits(world_map, "b2", "coal", 5)))

    def test_big_shallow_deposits_are_found_first(self):
        world_map = small_map()
        found_sizes, missed_sizes = [], []
        for seed in range(60):
            hidden = resources_prospecting.hidden_deposits(world_map, "b2", "coal", seed)
            found_ids = {deposit["id"] for deposit in resources_prospecting.prospect(world_map, "b2", "coal", 2000, seed)}
            for deposit in hidden:
                (found_sizes if deposit["id"] in found_ids else missed_sizes).append(deposit["ore_tonnes"])
        self.assertGreater(statistics.median(found_sizes), statistics.median(missed_sizes))

    def test_a_mod_resource_can_be_prospected(self):
        world_map = small_map(OVERLAY)
        total = sum(len(resources_prospecting.hidden_deposits(world_map, "a2", UNOBTAINIUM, seed)) for seed in range(50))
        self.assertGreater(total, 0)
        grades = [deposit["grade_per_tonne"] for seed in range(50)
                  for deposit in resources_prospecting.hidden_deposits(world_map, "a2", UNOBTAINIUM, seed)]
        self.assertTrue(all(grade > 0 for grade in grades))

    def test_a_biotic_stand_has_no_hidden_deposits(self):
        self.assertEqual(resources_prospecting.hidden_deposits(small_map(), "b1", "timber", 1), [])


class BioticTests(unittest.TestCase):
    def test_supports_follows_the_envelope(self):
        world_map = small_map()
        self.assertEqual(resources_biotic.supports(world_map, "b1", "timber"), 1.0)
        self.assertEqual(resources_biotic.supports(world_map, "a2", "timber"), 0.0)

    def test_stand_uses_the_fallback_cover_when_no_layer_exists(self):
        stand = resources_biotic.stand(small_map(), "b1", "timber")
        self.assertAlmostEqual(stand["stand_area_hectares"], 150000 * 100 * 0.5)
        self.assertAlmostEqual(stand["annual_regrowth"] / stand["standing_stock"], 0.04)

    def test_non_biotic_resource_is_rejected(self):
        with self.assertRaises(map_source.MapDataError):
            resources_biotic.supports(small_map(), "b1", "coal")

    def test_earth_timber_follows_the_measured_forest_layer(self):
        world_map = earth_map()
        forested = [tile for tile in world_map.tiles if tile_layers.number(world_map, tile, "forest_fraction", 0) > 0.8
                    and resources_biotic.supports(world_map, tile, "timber") > 0.5]
        self.assertTrue(forested)
        stand = resources_biotic.stand(world_map, forested[0], "timber")
        self.assertGreater(stand["standing_stock"], 0)
        deserts = [tile for tile in world_map.tiles if tile_layers.value(world_map, tile, "koppen_class") == "BWh"]
        self.assertTrue(all(resources_biotic.stand(world_map, tile, "timber")["standing_stock"] == 0 for tile in deserts))


class EarthTests(unittest.TestCase):
    def test_gold_is_orders_of_magnitude_richer_where_geology_has_it(self):
        world_map = earth_map()
        rich = resources_endowment.endowment(world_map, "south_africa_09", "gold")["total"]
        polar = [tile for tile in world_map.tiles if abs(world_map.tiles[tile]["lat"]) > 60]
        self.assertTrue(polar)
        for tile in polar:
            self.assertLess(resources_endowment.endowment(world_map, tile, "gold")["total"] * 100, rich)

    def test_giant_types_exist_only_near_known_deposits(self):
        world_map = earth_map()
        known = resources_catalogue.known_deposits(world_map, "gold")
        for tile_id, tile in world_map.tiles.items():
            nearest = min(haversine_km(tile["lat"], tile["lon"], deposit["lat"], deposit["lon"]) for deposit in known)
            if nearest > 1500:
                row = [row for row in resources_endowment.expected_counts(world_map, tile_id, "gold")
                       if row["deposit_type"] == "paleoplacer_conglomerate_gold"][0]
                self.assertLess(row["expected_count"], 0.002, tile_id)

    def test_small_coal_and_iron_workings_are_common_in_temperate_tiles(self):
        world_map = earth_map()
        temperate = [tile for tile in world_map.tiles if tile_layers.value(world_map, tile, "koppen_group") in ("C", "D")]
        for resource_id, small_types in (("coal", ("coal_seam_outcrop",)), ("iron", ("bog_iron", "gossan_skarn_vein_iron"))):
            enough = sum(1 for tile in temperate if sum(
                row["expected_count"] for row in resources_endowment.expected_counts(world_map, tile, resource_id)
                if row["deposit_type"] in small_types) >= 1.0)
            self.assertGreater(enough / len(temperate), 0.9, resource_id)

    def test_no_tile_exceeds_what_crustal_abundance_allows(self):
        world_map = earth_map()
        for resource_id in ("gold", "iron", "copper", "tin", "lead"):
            for tile_id in world_map.tiles:
                found = resources_endowment.endowment(world_map, tile_id, resource_id)
                self.assertLessEqual(found["undiscovered_expected"], found["ceiling"])
                self.assertLess(found["total"], found["ceiling"] / 1e-4)

    def test_diamonds_only_near_known_pipes_and_results_repeat(self):
        world_map = earth_map()
        near = resources_endowment.endowment(world_map, "south_africa_06", "diamond")
        far = resources_endowment.endowment(world_map, "germany_01", "diamond")
        self.assertGreater(near["total"], 1000 * max(far["total"], 1.0))
        self.assertEqual(resources_endowment.endowment(world_map, "south_africa_06", "diamond"), near)
        self.assertEqual(resources_prospecting.hidden_deposits(world_map, "south_africa_06", "diamond", 1),
                         resources_prospecting.hidden_deposits(world_map, "south_africa_06", "diamond", 1))

    def test_every_tile_summarises(self):
        world_map = earth_map()
        for tile_id in list(world_map.tiles)[::10]:
            summary = resources_summary.resources_at(world_map, tile_id)
            self.assertIsInstance(summary, dict)


if __name__ == "__main__":
    unittest.main()
