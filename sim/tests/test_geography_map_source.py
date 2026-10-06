"""Map folders merge under the mod rules, and per-tile values fall back from layers to fields to rules."""

QUICK_TOPIC = True

import os
import unittest

from sim.geography import content_rules, map_source, mechanisms, parameters, tile_layers

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geography_fixtures")
SMALL_MAP = os.path.join(FIXTURES, "small_map")
OVERLAY = (("test_overlay_k3f9", os.path.join(FIXTURES, "mod_overlay")),)


def small_map(overlays=()):
    return map_source.load_map(overlays, SMALL_MAP)


class MergeTests(unittest.TestCase):
    def test_base_map_loads_tiles_layers_and_catalogues(self):
        world_map = small_map()
        self.assertEqual(world_map.map_id, "test_small")
        self.assertEqual(len(world_map.tiles), 6)
        self.assertIn("gold", world_map.catalogue("resources"))

    def test_a_mod_adds_overrides_and_removes(self):
        resources = small_map(OVERLAY).catalogue("resources")
        self.assertIn("test_overlay_k3f9:unobtainium", resources)
        self.assertEqual(resources["gold"]["unit"], "troy_ounce")
        self.assertEqual(resources["gold"]["mechanism"], "mineral_deposit")
        self.assertNotIn("salt", resources)

    def test_a_mod_patches_one_tile_of_a_layer(self):
        world_map = small_map(OVERLAY)
        self.assertEqual(tile_layers.number(world_map, "a3", "annual_precipitation_mm"), 900)
        self.assertEqual(tile_layers.number(world_map, "a2", "annual_precipitation_mm"), 80)

    def test_a_mod_cannot_create_an_unnamespaced_id(self):
        with self.assertRaises(map_source.MapDataError):
            map_source._apply_entry({}, {"id": "plain"}, "some_mod_x1y2", "test.json")

    def test_override_of_a_missing_id_fails_with_the_file_named(self):
        with self.assertRaisesRegex(map_source.MapDataError, "test.json"):
            map_source._apply_entry({}, {"id": "nothing", "override": True}, None, "test.json")

    def test_null_in_an_override_deletes_the_key(self):
        merged = map_source.deep_merge({"a": 1, "b": {"c": 2, "d": 3}}, {"b": {"c": None}})
        self.assertEqual(merged, {"a": 1, "b": {"d": 3}})


class LayerTests(unittest.TestCase):
    def test_layer_then_field_then_rule(self):
        world_map = small_map()
        self.assertEqual(tile_layers.number(world_map, "a1", "annual_precipitation_mm"), 600)
        self.assertIsNone(tile_layers.value(world_map, "b3", "annual_precipitation_mm"))
        self.assertEqual(tile_layers.value(world_map, "a2", "koppen_group"), "B")
        self.assertEqual(tile_layers.value(world_map, "b2", "biome"), "boreal_forest")


class RuleTests(unittest.TestCase):
    def test_conditions(self):
        lookup = tile_layers.reader(small_map(), "a2")
        self.assertTrue(content_rules.matches([{"layer": "koppen_group", "in": ["B"]}], lookup))
        self.assertFalse(content_rules.matches([{"layer": "annual_precipitation_mm", "min": 200}], lookup))
        self.assertFalse(content_rules.matches([{"layer": "nonexistent", "min": 0}], lookup))

    def test_envelope_ramps_between_optimal_and_tolerated(self):
        envelope = [{"layer": "annual_precipitation_mm", "optimal": [500, 1000], "tolerated": [100, 2000]}]
        world_map = small_map()
        self.assertEqual(content_rules.suitability(envelope, tile_layers.reader(world_map, "a1")), 1.0)
        self.assertEqual(content_rules.suitability(envelope, tile_layers.reader(world_map, "a3")), 0.0)
        self.assertAlmostEqual(content_rules.suitability(
            envelope, lambda name: 300), 0.5)


class EarthMapTests(unittest.TestCase):
    def test_every_parameter_states_kind_source_and_reason(self):
        self.assertEqual(parameters.invalid_entries(map_source.load_map()), [])

    def test_every_resource_row_names_a_known_mechanism(self):
        self.assertEqual(mechanisms.unknown_rows(map_source.load_map()), [])

    def test_every_tile_has_a_climate_group(self):
        world_map = map_source.load_map()
        missing = [tile_id for tile_id in world_map.tiles if not tile_layers.value(world_map, tile_id, "koppen_group")]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
