"""Category traits are data: the engine reads them per category, and a mod can add a category."""
QUICK_TOPIC = True

import json
import tempfile
import unittest
from pathlib import Path

from sim.diffusion import rules
from sim.diffusion.module import Diffusion
from sim.engine import category_traits
from sim.knowledge.module import Knowledge
from sim.engine.tree_source import load_base_tree
from sim.tests import module_harness, production_host


class CategoriesReadTheirTraits(unittest.TestCase):
    def setUp(self):
        self.nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        self.categories = sorted({node["cat"] for node in self.nodes.values() if node.get("cat")})

    def test_diffusion_category_of_a_node_carrying_two_traits(self):
        self.assertEqual("food", rules.diffusion_category(["medical", "food"], category_traits.diffusion_trait_names()))

    def test_every_node_category_has_an_entry(self):
        self.assertEqual([], category_traits.categories_without_traits(self.nodes.values()))


class ModAddsCategory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mods_dir = Path(self.tmp.name)
        folder = self.mods_dir / "test_cat_k3f9" / "data"
        folder.mkdir(parents=True)
        (self.mods_dir / "test_cat_k3f9" / "mod.json").write_text(json.dumps({
            "id": "test_cat_k3f9", "name": "c", "version": "1", "dependencies": [], "conflicts": []}))
        (folder / "category_traits.json").write_text(json.dumps({
            "categories": {"test_cat_k3f9:rites": {"never_abandoned": True, "practisable": True},
                           "dentistry": {"practisable": False}},
            "diffusion_traits": [{"trait": "ritual", "half_life_years": 50.0, "text_paced": True}]}))
        self.saved = category_traits.MODS_DIRECTORY
        category_traits.MODS_DIRECTORY = str(self.mods_dir)

    def tearDown(self):
        category_traits.MODS_DIRECTORY = self.saved
        self.tmp.cleanup()

    def production(self, nodes):
        return production_host.build(tree_nodes=nodes, category_trait=category_traits.has_trait)

    def test_new_category_trait_takes_effect_in_engine(self):
        nodes = {"x": {"cat": "test_cat_k3f9:rites", "traits": []}}
        self.assertTrue(category_traits.has_trait("test_cat_k3f9:rites", "never_abandoned"))
        self.assertTrue(self.production(nodes)._practisable("x"))
        self.assertEqual([], category_traits.categories_without_traits(nodes.values()))

    def test_override_of_existing_category(self):
        nodes = {"x": {"cat": "dentistry"}}
        self.assertFalse(self.production(nodes)._practisable("x"))

    def test_new_diffusion_trait_is_last_and_usable(self):
        names = category_traits.diffusion_trait_names()
        self.assertEqual("ritual", names[-1])
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual("ritual", rules.diffusion_category(["ritual"], names))
        module = module_harness.build(Diffusion, views={"diffusion_traits": category_traits.diffusion_traits()})
        self.assertEqual(50.0, module.category_half_life_years("ritual"))

    def test_unlisted_category_is_reported(self):
        nodes = [{"id": "y", "cat": "test_cat_k3f9:unlisted"}]
        self.assertEqual(["test_cat_k3f9:unlisted"], category_traits.categories_without_traits(nodes))


class FogUsesTraits(unittest.TestCase):
    def test_protected_category(self):
        knowledge = module_harness.build(Knowledge, views={
            "legacy_tree": {"a": {"cat": "physics"}, "b": {"cat": "rail"}}, "category_trait": category_traits.has_trait,
            "on_road_to_goal": lambda node_id: False, "relied_on_running": lambda node_id: False})
        self.assertTrue(knowledge.never_abandon("a"))
        self.assertFalse(knowledge.never_abandon("b"))


if __name__ == "__main__":
    unittest.main()
