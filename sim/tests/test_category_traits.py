"""Category traits are data: engine behaviour per category is unchanged, and a mod can add a category."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from sim.engine import category_traits
from sim.engine.economy_production import ProductionMixin
from sim.engine.fog import FogMixin
from sim.engine.society_diffusion import DiffusionMixin
from sim.engine.tree_source import load_base_tree

# The sets the engine enumerated before they became data.
FORMER_NEVER_ABANDON = {"mathematics", "physics", "method", "notation", "algebra", "geometry",
                        "probability", "analysis", "theory", "knowledge"}
FORMER_PRACTISABLE = {"surgery", "obstetrics", "pharmacology", "medicine", "diagnosis", "dentistry"}
FORMER_DIFFUSION_PRIORITY = ("food", "medical", "military", "information")


class ExistingCategoriesUnchanged(unittest.TestCase):
    def setUp(self):
        self.nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
        self.categories = sorted({node["cat"] for node in self.nodes.values() if node.get("cat")})

    def test_never_abandoned_membership(self):
        for category in self.categories:
            self.assertEqual(category in FORMER_NEVER_ABANDON,
                             category_traits.has_trait(category, "never_abandoned"), category)

    def test_practisable_membership(self):
        stub = SimpleNamespace(nodes=self.nodes)
        for node_id, node in self.nodes.items():
            self.assertEqual(node.get("cat") in FORMER_PRACTISABLE,
                             ProductionMixin._practisable(stub, node_id), node_id)

    def test_diffusion_priority_order(self):
        self.assertEqual(FORMER_DIFFUSION_PRIORITY, category_traits.diffusion_trait_names())

    def test_diffusion_category_of_a_node_carrying_two_traits(self):
        stub = SimpleNamespace()
        self.assertEqual("food", DiffusionMixin._diffusion_category(stub, {"traits": ["medical", "food"]}))

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

    def test_new_category_trait_takes_effect_in_engine(self):
        nodes = {"x": {"cat": "test_cat_k3f9:rites", "traits": []}}
        self.assertTrue(category_traits.has_trait("test_cat_k3f9:rites", "never_abandoned"))
        self.assertTrue(ProductionMixin._practisable(SimpleNamespace(nodes=nodes), "x"))
        self.assertEqual([], category_traits.categories_without_traits(nodes.values()))

    def test_override_of_existing_category(self):
        nodes = {"x": {"cat": "dentistry"}}
        self.assertFalse(ProductionMixin._practisable(SimpleNamespace(nodes=nodes), "x"))

    def test_new_diffusion_trait_is_last_and_usable(self):
        self.assertEqual(FORMER_DIFFUSION_PRIORITY + ("ritual",), category_traits.diffusion_trait_names())
        self.assertEqual("ritual", DiffusionMixin._diffusion_category(SimpleNamespace(), {"traits": ["ritual"]}))
        self.assertEqual(50.0, DiffusionMixin._diffusion_half_life_years(SimpleNamespace(), "ritual"))

    def test_unlisted_category_is_reported(self):
        nodes = [{"id": "y", "cat": "test_cat_k3f9:unlisted"}]
        self.assertEqual(["test_cat_k3f9:unlisted"], category_traits.categories_without_traits(nodes))


class FogUsesTraits(unittest.TestCase):
    def test_protected_category(self):
        stub = SimpleNamespace(nodes={"a": {"cat": "physics"}, "b": {"cat": "rail"}},
                               on_road_to_goal=lambda node_id: False)
        self.assertTrue(FogMixin.never_abandon(stub, "a"))
        self.assertFalse(FogMixin.never_abandon(stub, "b"))


if __name__ == "__main__":
    unittest.main()
