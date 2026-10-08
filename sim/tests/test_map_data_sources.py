"""The map generators' dataset registry covers every layer, names each default's dataset and drives the build."""

QUICK_TOPIC = True

import json
import os
import unittest
from unittest import mock

from sim.geography import map_data_sources
from sim.geography.layer_build import catalog, compute

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEOGRAPHY = os.path.join(ROOT, "data", "world", "geography")
SEA_LINKS = "sea_links"


def layer_ids_on_disk():
    directory = os.path.join(GEOGRAPHY, "layers")
    return {name[:-5] for name in os.listdir(directory) if name.endswith(".json")}


def stub_loader(tiles, cache_dir, source):
    return {"stub_called_with": (tiles, cache_dir, source.dataset)}


STUB_SOURCE = map_data_sources.Source("Stub dataset", "nobody", "none", "", "none",
                                      "sim.tests.test_map_data_sources:stub_loader", "stub text", {})


class MapDataSourceTests(unittest.TestCase):
    def test_registry_covers_every_layer_written(self):
        expected = layer_ids_on_disk() | set(map_data_sources.TILE_GRID_LAYERS) | {SEA_LINKS}
        self.assertEqual(set(map_data_sources.SOURCES), expected)
        self.assertLessEqual(set(catalog.LAYERS), set(map_data_sources.SOURCES))

    def test_every_default_names_its_dataset(self):
        for layer, options in map_data_sources.SOURCES.items():
            default = options[map_data_sources.default_option(layer)]
            for field in (default.dataset, default.provider, default.citation):
                self.assertTrue(field.strip(), layer)

    def test_default_source_text_is_what_the_committed_layer_file_records(self):
        for layer in layer_ids_on_disk():
            with open(os.path.join(GEOGRAPHY, "layers", layer + ".json"), encoding="utf-8") as handle:
                recorded = json.load(handle)["source"]
            default = map_data_sources.SOURCES[layer][map_data_sources.default_option(layer)]
            self.assertEqual(default.source_text, recorded, layer)

    def test_every_default_loader_exists(self):
        for layer, options in map_data_sources.SOURCES.items():
            for source in options.values():
                if not source.loader:
                    continue  # tile-grid shapefile sources are read by their files, not a loader
                module_name, _, function_name = source.loader.partition(":")
                path = os.path.join(ROOT, *module_name.split(".")) + ".py"
                with open(path, encoding="utf-8") as handle:
                    self.assertIn("def %s(" % function_name, handle.read(), layer)

    def test_natural_earth_downloads_come_from_the_registry(self):
        land = map_data_sources.SOURCES["land_mask"][map_data_sources.default_option("land_mask")]
        self.assertTrue(land.files["url"].startswith(land.files["base"]))
        self.assertTrue(land.files["shapefile"].endswith(".shp"))

    def test_koppen_default_is_rubel_not_beck(self):
        default = map_data_sources.SOURCES["koppen_class"][map_data_sources.default_option("koppen_class")]
        self.assertIn("Rubel", default.dataset)

    def test_overrides_are_validated(self):
        with mock.patch.dict(map_data_sources.SOURCES["mean_temperature_c"], {"stub": STUB_SOURCE}):
            chosen = map_data_sources.resolve_sources(["mean_temperature_c=stub"])
            self.assertEqual(chosen["mean_temperature_c"], "stub")
        with self.assertRaises(ValueError):
            map_data_sources.resolve_sources(["mean_temperature_c=nonexistent"])
        with self.assertRaises(ValueError):
            map_data_sources.resolve_sources(["no_such_layer=x"])

    def test_the_chosen_option_is_the_loader_that_runs(self):
        with mock.patch.dict(map_data_sources.SOURCES["mean_temperature_c"], {"stub": STUB_SOURCE}):
            values = compute.compute_layer("mean_temperature_c", "stub", ["tile"], None, "cache")
        self.assertEqual(values, {"stub_called_with": (["tile"], "cache", "Stub dataset")})

    def test_attribution_file_lists_every_layer(self):
        with open(os.path.join(GEOGRAPHY, "ATTRIBUTION.md"), encoding="utf-8") as handle:
            text = handle.read()
        for layer in map_data_sources.SOURCES:
            self.assertIn("| %s |" % layer, text)


if __name__ == "__main__":
    unittest.main()
