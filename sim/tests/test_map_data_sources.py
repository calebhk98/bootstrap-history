"""The map generators' dataset registry covers every layer and names each default's dataset."""

QUICK_TOPIC = True

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import koppen_classifiers  # noqa: E402
import map_data_sources  # noqa: E402

GEOGRAPHY = os.path.join(ROOT, "data", "world", "geography")


def layer_ids_on_disk():
    directory = os.path.join(GEOGRAPHY, "layers")
    return {name[:-5] for name in os.listdir(directory) if name.endswith(".json")}


class MapDataSourceTests(unittest.TestCase):
    def test_registry_covers_every_layer_written(self):
        expected = layer_ids_on_disk() | set(map_data_sources.TILE_GRID_LAYERS)
        self.assertEqual(set(map_data_sources.SOURCES), expected)

    def test_every_layer_has_options_and_default_names_its_dataset(self):
        for layer, options in map_data_sources.SOURCES.items():
            self.assertTrue(options, layer)
            default = options[map_data_sources.default_option(layer)]
            self.assertTrue(default.dataset.strip(), layer)
            self.assertTrue(default.provider.strip(), layer)
            self.assertTrue(default.citation.strip(), layer)

    def test_default_dataset_matches_the_committed_layer_file(self):
        import json
        for layer in layer_ids_on_disk():
            with open(os.path.join(GEOGRAPHY, "layers", layer + ".json"), encoding="utf-8") as handle:
                recorded = json.load(handle)["source"]
            provider = map_data_sources.SOURCES[layer][map_data_sources.default_option(layer)].dataset.split(" ")[0]
            self.assertIn(provider, recorded, layer)

    def test_every_koppen_option_has_a_classifier(self):
        self.assertEqual(set(map_data_sources.SOURCES["koppen_class"]), set(koppen_classifiers.KOPPEN_CLASSIFIERS))

    def test_koppen_default_is_rubel_not_beck(self):
        default = map_data_sources.SOURCES["koppen_class"][map_data_sources.default_option("koppen_class")]
        self.assertIn("Rubel", default.dataset)

    def test_overrides_are_validated(self):
        chosen = map_data_sources.resolve_sources(["koppen_class=kgcpy_rubel_2016"])
        self.assertEqual(chosen["koppen_class"], "kgcpy_rubel_2016")
        with self.assertRaises(ValueError):
            map_data_sources.resolve_sources(["koppen_class=nonexistent"])
        with self.assertRaises(ValueError):
            map_data_sources.resolve_sources(["no_such_layer=x"])

    def test_attribution_file_lists_every_layer(self):
        with open(os.path.join(GEOGRAPHY, "ATTRIBUTION.md"), encoding="utf-8") as handle:
            text = handle.read()
        for layer in map_data_sources.SOURCES:
            self.assertIn("| %s |" % layer, text)
