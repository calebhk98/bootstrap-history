"""Category traits are data: the engine reads them per category, and a mod can add a category."""
QUICK_TOPIC = True

import json
import tempfile
import unittest
from pathlib import Path

from sim.diffusion import rules
from sim.diffusion.module import Diffusion
from sim.knowledge import category_traits
from sim.knowledge.api import ReplaceTree
from sim.knowledge.module import Knowledge
from sim.content.tree_source import load_base_tree
from sim.tests import module_harness, production_host

NO_MODS = "/nonexistent-mods-directory"


class CategoriesReadTheirTraits(unittest.TestCase):
    def setUp(self):
        self.nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        self.catalogue = category_traits.load(NO_MODS)

    def test_diffusion_category_of_a_node_carrying_two_traits(self):
        names = tuple(category_traits.diffusion_traits(self.catalogue))
        self.assertEqual("food", rules.diffusion_category(["medical", "food"], names))

    def test_every_node_category_has_an_entry(self):
        self.assertEqual([], category_traits.categories_without_traits(self.catalogue, self.nodes.values()))

    def test_a_category_with_no_entry_has_no_trait(self):
        self.assertFalse(category_traits.has_trait({"categories": {}}, "anything", "never_abandoned"))


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
        self.catalogue = category_traits.load(str(self.mods_dir))

    def tearDown(self):
        self.tmp.cleanup()

    def production(self, nodes):
        return production_host.build(
            tree_nodes=nodes, category_trait=lambda category, trait: category_traits.has_trait(self.catalogue, category, trait))

    def test_new_category_trait_takes_effect_in_engine(self):
        nodes = {"x": {"cat": "test_cat_k3f9:rites", "traits": []}}
        self.assertTrue(category_traits.has_trait(self.catalogue, "test_cat_k3f9:rites", "never_abandoned"))
        self.assertTrue(self.production(nodes)._practisable("x"))
        self.assertEqual([], category_traits.categories_without_traits(self.catalogue, nodes.values()))

    def test_override_of_existing_category(self):
        nodes = {"x": {"cat": "dentistry"}}
        self.assertFalse(self.production(nodes)._practisable("x"))

    def test_new_diffusion_trait_is_last_and_usable(self):
        names = tuple(category_traits.diffusion_traits(self.catalogue))
        self.assertEqual("ritual", names[-1])
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual("ritual", rules.diffusion_category(["ritual"], names))
        module = module_harness.build(Diffusion, views={"diffusion_traits": category_traits.diffusion_traits(self.catalogue)})
        self.assertEqual(50.0, module.category_half_life_years("ritual"))

    def test_base_diffusion_traits_keep_their_order_before_the_mods(self):
        base = tuple(category_traits.diffusion_traits(category_traits.load(NO_MODS)))
        self.assertEqual(base, tuple(category_traits.diffusion_traits(self.catalogue))[:len(base)])

    def test_unlisted_category_is_reported(self):
        nodes = [{"id": "y", "cat": "test_cat_k3f9:unlisted"}]
        self.assertEqual(["test_cat_k3f9:unlisted"], category_traits.categories_without_traits(self.catalogue, nodes))

    def test_the_check_names_a_category_with_no_entry(self):
        problems = category_traits.check_category_traits([{"id": "y", "cat": "test_cat_k3f9:unlisted"}], str(self.mods_dir))
        self.assertEqual(1, len(problems))


class KnowledgeAnswersTraitsOverItsGamesMods(unittest.TestCase):
    def knowledge(self, mods_directory):
        module = module_harness.build(Knowledge, views={
            "mods_directory": mods_directory, "on_road_to_goal": lambda node_id: False, "relied_on_running": lambda node_id: False})
        module.replace_tree(ReplaceTree({"a": {"cat": "physics"}, "b": {"cat": "rail"}}))
        return module

    def test_protected_category(self):
        module = self.knowledge(NO_MODS)
        self.assertTrue(module.never_abandon("a"))
        self.assertFalse(module.never_abandon("b"))

    def test_the_view_answers_the_flag_of_the_category(self):
        module = self.knowledge(NO_MODS)
        self.assertTrue(module.category_trait("physics", "never_abandoned"))
        self.assertFalse(module.category_trait("rail", "never_abandoned"))

    def test_the_view_lists_the_diffusion_traits_as_the_loader_orders_them(self):
        module = self.knowledge(NO_MODS)
        self.assertEqual(list(category_traits.diffusion_traits(category_traits.load(NO_MODS))), list(module.diffusion_traits()))


class KnowledgeHoldsTheTree(unittest.TestCase):
    def test_a_replaced_tree_is_the_object_given_and_a_missing_node_is_none(self):
        module = module_harness.build(Knowledge, views={})
        tree = {"a": {"cat": "x"}}
        module.replace_tree(ReplaceTree(tree))
        self.assertIs(tree, module.tree_nodes())
        self.assertEqual({"cat": "x"}, module.tree("a"))
        self.assertIsNone(module.tree("b"))

    def test_a_second_tree_replaces_the_first(self):
        module = module_harness.build(Knowledge, views={})
        module.replace_tree(ReplaceTree({"a": {}}))
        module.replace_tree(ReplaceTree({"b": {}}))
        self.assertEqual(["b"], list(module.tree_nodes()))


if __name__ == "__main__":
    unittest.main()
