"""Override semantics and error reporting for the mod tree and production loaders.

Mod loader override semantics and error reporting (unittest-style).
"""

QUICK_TOPIC = True

import copy
import json
from pathlib import Path
import tempfile
import unittest

from sim.engine.mods import ModError, get_ordered_mods, load_mod_production, load_mod_tree


BASE_NODE = {"id": "mat_copper", "name": "Copper", "cat": "material", "note": "", "cap_hours": 100,
             "pre": ["mat_ore"], "risk": 0.4, "traits": ["metal"], "up_hours": 7, "yrs": 3.0,
             "lab": {"smith": 2}, "mat": {"ore": 1}}
BASE_TREE = {"nodes": [BASE_NODE, {**BASE_NODE, "id": "mat_ore"}], "meta": {"goals": []}}
BASE_RECIPE = {"outputs": {"copper": 1}, "inputs": {"ore": 2}, "labour_hours": {"smith": 1}}


class ModOverrideTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mods_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def add_mod(self, mod_id, dependencies=(), nodes=None, recipes=None):
        folder = self.mods_dir / mod_id
        (folder / "data/branches").mkdir(parents=True)
        (folder / "data/production").mkdir(parents=True)
        (folder / "mod.json").write_text(json.dumps({
            "id": mod_id, "name": mod_id, "version": "1",
            "dependencies": list(dependencies), "conflicts": []}))
        if nodes is not None:
            (folder / "data/branches/nodes.json").write_text(json.dumps({"nodes": nodes}))
        if recipes is not None:
            (folder / "data/production/recipes.json").write_text(json.dumps({"materials": recipes}))

    def tree(self):
        return {node["id"]: node for node in load_mod_tree(
            copy.deepcopy(BASE_TREE), get_ordered_mods(str(self.mods_dir)))["nodes"]}

    def production(self):
        return load_mod_production({"copper": copy.deepcopy(BASE_RECIPE)},
                                   get_ordered_mods(str(self.mods_dir)))

    def test_override_changes_only_named_fields(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "mat_copper", "override": True, "cap_hours": 222}])
        node = self.tree()["mat_copper"]
        self.assertEqual(222, node["cap_hours"])
        for field in ("pre", "risk", "traits", "up_hours", "yrs", "lab", "mat", "name"):
            self.assertEqual(BASE_NODE[field], node[field], field)

    def test_replaces_patches_only_named_fields(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "test_acme_k3f9:x", "replaces": "mat_copper", "risk": 0.9}])
        nodes = self.tree()
        self.assertEqual(0.9, nodes["mat_copper"]["risk"])
        self.assertEqual(["mat_ore"], nodes["mat_copper"]["pre"])
        self.assertNotIn("test_acme_k3f9:x", nodes)

    def test_new_node_still_gets_defaults(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "test_acme_k3f9:thing", "name": "Thing"}])
        node = self.tree()["test_acme_k3f9:thing"]
        self.assertEqual([], node["pre"])
        self.assertEqual(0.15, node["risk"])

    def test_recipe_override_changes_only_named_fields(self):
        self.add_mod("test_acme_k3f9", recipes={"copper": {"override": True, "labour_hours": {"smith": 3}}})
        recipe = self.production()["copper"]
        self.assertEqual({"smith": 3}, recipe["labour_hours"])
        self.assertEqual(BASE_RECIPE["inputs"], recipe["inputs"])
        self.assertEqual(BASE_RECIPE["outputs"], recipe["outputs"])

    def test_two_mods_overriding_same_node_field_is_an_error(self):
        for mod_id, cap in (("test_acme_k3f9", 1), ("test_zeta_k3f9", 2)):
            self.add_mod(mod_id, nodes=[{"id": "mat_copper", "override": True, "cap_hours": cap}])
        with self.assertRaises(ModError) as caught:
            self.tree()
        for word in ("test_acme_k3f9", "test_zeta_k3f9", "mat_copper", "cap_hours"):
            self.assertIn(word, str(caught.exception))

    def test_two_mods_overriding_different_fields_is_fine(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "mat_copper", "override": True, "cap_hours": 1}])
        self.add_mod("test_zeta_k3f9", nodes=[{"id": "mat_copper", "override": True, "risk": 0.5}])
        node = self.tree()["mat_copper"]
        self.assertEqual((1, 0.5), (node["cap_hours"], node["risk"]))

    def test_dependent_mod_wins_deliberately(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "mat_copper", "override": True, "cap_hours": 1}])
        self.add_mod("test_zeta_k3f9", dependencies=["test_acme_k3f9"],
                     nodes=[{"id": "mat_copper", "override": True, "cap_hours": 2}])
        self.assertEqual(2, self.tree()["mat_copper"]["cap_hours"])

    def test_two_mods_overriding_same_recipe_field_is_an_error(self):
        for mod_id, hours in (("test_acme_k3f9", 1), ("test_zeta_k3f9", 2)):
            self.add_mod(mod_id, recipes={"copper": {"override": True,
                                                     "labour_hours": {"smith": hours}}})
        with self.assertRaises(ModError) as caught:
            self.production()
        for word in ("test_acme_k3f9", "test_zeta_k3f9", "copper", "labour_hours"):
            self.assertIn(word, str(caught.exception))

    def test_dependent_recipe_override_wins(self):
        self.add_mod("test_acme_k3f9", recipes={"copper": {"override": True, "inputs": {"ore": 1}}})
        self.add_mod("test_zeta_k3f9", dependencies=["test_acme_k3f9"],
                     recipes={"copper": {"override": True, "inputs": {"ore": 5}}})
        self.assertEqual({"ore": 5}, self.production()["copper"]["inputs"])

    def test_malformed_node_names_mod_and_file(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "test_acme_k3f9:thing"}])
        with self.assertRaises(ModError) as caught:
            self.tree()
        self.assertIn("test_acme_k3f9", str(caught.exception))
        self.assertIn("nodes.json", str(caught.exception))
        self.assertIn("name", str(caught.exception))

    def test_non_object_node_is_a_mod_error(self):
        self.add_mod("test_acme_k3f9", nodes=["test_acme_k3f9:thing"])
        with self.assertRaises(ModError):
            self.tree()


if __name__ == "__main__":
    unittest.main()
