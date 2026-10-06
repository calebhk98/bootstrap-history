"""Mod removal of content and patching or hiding of base civilisations."""

QUICK_TOPIC = True

import copy
import json
from pathlib import Path
from unittest import mock
import tempfile
import unittest

from sim.engine import data
from sim.engine.catalog import (load_production_catalog, load_trade_registry,
                                validate_mod_material_paths)
from sim.engine.mods import ModError, get_ordered_mods, load_mod_production, load_mod_tree


def node(node_id, pre=(), **extra):
    return {"id": node_id, "name": node_id, "pre": list(pre), "lab": {}, "mat": {}, **extra}


BASE_TREE = {"nodes": [node("a"), node("b", ["a"]), node("c", ["b"]),
                       node("d", req_any=[{"group": "g", "options": {"b": 1.0}}])],
             "meta": {"goals": [{"node": "c", "name": "C"}, {"node": "a", "name": "A"}],
                      "goal_node": "c"}}
BASE_RECIPES = {"copper": {"outputs": {"copper": 1}, "inputs": {"ore": 2},
                           "labour_hours": {"smith": 1}},
                "ore": {"outputs": {"ore": 1}, "inputs": {}, "labour_hours": {"smith": 1}}}


class ModTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.mods_dir = self.root / "mods"

    def tearDown(self):
        self.tmp.cleanup()

    def add_mod(self, mod_id, dependencies=(), nodes=None, recipes=None, goals=None,
                trades=None, civs=None):
        folder = self.mods_dir / mod_id
        for sub in ("branches", "production", "world", "civilizations"):
            (folder / "data" / sub).mkdir(parents=True, exist_ok=True)
        (folder / "mod.json").write_text(json.dumps({
            "id": mod_id, "name": mod_id, "version": "1",
            "dependencies": list(dependencies), "conflicts": []}))
        if nodes is not None:
            (folder / "data/branches/n.json").write_text(json.dumps({"nodes": nodes}))
        if recipes is not None:
            (folder / "data/production/r.json").write_text(json.dumps({"materials": recipes}))
        if goals is not None:
            (folder / "data/goals.json").write_text(json.dumps({"goals": goals}))
        if trades is not None:
            (folder / "data/world/trades.json").write_text(json.dumps({"trades": trades}))
        for civ_id, civ in (civs or {}).items():
            (folder / "data/civilizations" / (civ_id.replace(":", "+") + ".json")).write_text(json.dumps(civ))

    def manifests(self):
        return get_ordered_mods(str(self.mods_dir))

    def tree(self):
        return {found["id"]: found for found in
                load_mod_tree(copy.deepcopy(BASE_TREE), self.manifests())["nodes"]}

    def production(self):
        return load_mod_production(copy.deepcopy(BASE_RECIPES), self.manifests())


class RemovalTests(ModTestBase):
    def test_remove_tech_node(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "d", "remove": True}])
        self.assertNotIn("d", self.tree())

    def test_remove_missing_id_is_an_error(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "nope", "remove": True}])
        with self.assertRaises(ModError) as caught:
            self.tree()
        self.assertIn("nope", str(caught.exception))

    def test_dangling_prerequisite_names_item_and_mod(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "b", "remove": True}])
        with self.assertRaises(ModError) as caught:
            self.tree()
        for word in ("c", "b", "test_acme_k3f9"):
            self.assertIn(word, str(caught.exception))

    def test_dangling_req_any_option_is_an_error(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "b", "remove": True}, {"id": "c", "remove": True},
                                    {"id": "a", "override": True, "cap_hours": 1}],
                     goals=[{"node": "c", "remove": True}])
        with self.assertRaises(ModError) as caught:
            self.tree()
        self.assertIn("d", str(caught.exception))

    def test_reference_patched_away_by_same_mod_is_fine(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "b", "remove": True},
                                    {"id": "c", "override": True, "pre": ["a"]},
                                    {"id": "d", "override": True, "req_any": []}])
        self.assertNotIn("b", self.tree())

    def test_reference_patched_away_by_dependent_mod_is_fine(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "b", "remove": True}])
        self.add_mod("test_zeta_k3f9", dependencies=["test_acme_k3f9"],
                     nodes=[{"id": "c", "override": True, "pre": []},
                            {"id": "d", "override": True, "req_any": []}])
        self.assertNotIn("b", self.tree())

    def test_dangling_goal_is_an_error(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "a", "remove": True}])
        with self.assertRaises(ModError) as caught:
            self.tree()
        self.assertIn("test_acme_k3f9", str(caught.exception))

    def test_remove_goal(self):
        self.add_mod("test_acme_k3f9", goals=[{"node": "c", "remove": True}])
        goals = load_mod_tree(copy.deepcopy(BASE_TREE), self.manifests())["meta"]["goals"]
        self.assertEqual(["a"], [goal["node"] for goal in goals])

    def test_remove_missing_goal_is_an_error(self):
        self.add_mod("test_acme_k3f9", goals=[{"node": "d", "remove": True}])
        with self.assertRaises(ModError):
            self.tree()

    def test_remove_recipe(self):
        self.add_mod("test_acme_k3f9", recipes={"copper": {"remove": True}})
        self.assertNotIn("copper", self.production())

    def test_remove_missing_recipe_is_an_error(self):
        self.add_mod("test_acme_k3f9", recipes={"gold": {"remove": True}})
        with self.assertRaises(ModError):
            self.production()

    def test_dangling_recipe_input_is_an_error(self):
        self.add_mod("test_acme_k3f9", recipes={"ore": {"remove": True}})
        with self.assertRaises(ModError) as caught:
            self.production()
        for word in ("copper", "ore", "test_acme_k3f9"):
            self.assertIn(word, str(caught.exception))

    def test_recipe_input_patched_away_with_null(self):
        self.add_mod("test_acme_k3f9", recipes={"ore": {"remove": True},
                                      "copper": {"override": True, "inputs": {"ore": None}}})
        self.assertEqual({}, self.production()["copper"]["inputs"])

    def test_technology_material_of_removed_recipe_is_an_error(self):
        self.add_mod("test_acme_k3f9", recipes={"ore": {"remove": True},
                                      "copper": {"override": True, "inputs": {"ore": None}}})
        production = self.production()
        nodes = [node("x", mat={"ore": 1})]
        with self.assertRaises(ModError) as caught:
            validate_mod_material_paths(nodes, production, self.manifests())
        self.assertIn("test_acme_k3f9", str(caught.exception))

    def test_remove_versus_override_by_unrelated_mods_names_both(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "d", "remove": True}])
        self.add_mod("test_zeta_k3f9", nodes=[{"id": "d", "override": True, "cap_hours": 3}])
        with self.assertRaises(ModError) as caught:
            self.tree()
        for word in ("test_acme_k3f9", "test_zeta_k3f9", "d"):
            self.assertIn(word, str(caught.exception))

    def test_override_then_remove_by_unrelated_mods_names_both(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "d", "override": True, "cap_hours": 3}])
        self.add_mod("test_zeta_k3f9", nodes=[{"id": "d", "remove": True}])
        with self.assertRaises(ModError) as caught:
            self.tree()
        for word in ("test_acme_k3f9", "test_zeta_k3f9"):
            self.assertIn(word, str(caught.exception))

    def test_dependent_mod_may_remove_what_dependency_overrode(self):
        self.add_mod("test_acme_k3f9", nodes=[{"id": "d", "override": True, "cap_hours": 3}])
        self.add_mod("test_zeta_k3f9", dependencies=["test_acme_k3f9"], nodes=[{"id": "d", "remove": True}])
        self.assertNotIn("d", self.tree())

    def test_recipe_remove_versus_override_by_unrelated_mods(self):
        self.add_mod("test_acme_k3f9", recipes={"copper": {"remove": True}})
        self.add_mod("test_zeta_k3f9", recipes={"copper": {"override": True, "inputs": {"ore": 5}}})
        with self.assertRaises(ModError) as caught:
            self.production()
        for word in ("test_acme_k3f9", "test_zeta_k3f9"):
            self.assertIn(word, str(caught.exception))


class TradeRemovalTests(ModTestBase):
    def setUp(self):
        super().setUp()
        (self.root / "data/world").mkdir(parents=True)
        (self.root / "data/production").mkdir(parents=True)
        (self.root / "data/world/trades.json").write_text(json.dumps({"trades": {
            "smith": {"family": "craft"}, "scribe": {"family": "scholar"}}}))
        (self.root / "data/production/base.json").write_text(json.dumps({"materials": {
            "ore": {"outputs": {"ore": 1}, "inputs": {}, "labour_hours": {"smith": 1}}}}))

    def registry(self, nodes=()):
        production = load_production_catalog(str(self.root), str(self.mods_dir),
                                             manifests=self.manifests())
        return load_trade_registry(str(self.root), production, str(self.mods_dir), nodes=nodes)

    def test_remove_unused_trade(self):
        self.add_mod("test_acme_k3f9", trades={"scribe": {"remove": True}})
        self.assertNotIn("scribe", self.registry())

    def test_remove_missing_trade_is_an_error(self):
        self.add_mod("test_acme_k3f9", trades={"baker": {"remove": True}})
        with self.assertRaises(ModError):
            self.registry()

    def test_recipe_using_removed_trade_is_an_error(self):
        self.add_mod("test_acme_k3f9", trades={"smith": {"remove": True}})
        with self.assertRaises(ModError) as caught:
            self.registry()
        for word in ("ore", "smith", "test_acme_k3f9"):
            self.assertIn(word, str(caught.exception))

    def test_technology_using_removed_trade_is_an_error(self):
        self.add_mod("test_acme_k3f9", trades={"scribe": {"remove": True}})
        with self.assertRaises(ModError) as caught:
            self.registry(nodes=[node("x", lab={"scribe": 1})])
        self.assertIn("x", str(caught.exception))

    def test_recipe_patched_away_from_removed_trade(self):
        self.add_mod("test_acme_k3f9", trades={"smith": {"remove": True}},
                     recipes={"ore": {"override": True,
                                      "labour_hours": {"smith": None, "labourer": 1}}})
        self.assertNotIn("smith", self.registry())


def rome_patch(**fields):
    return {"override": True, **fields}


class CivilizationModTests(ModTestBase):
    def load(self, name="rome_100ad"):
        with mock.patch.object(data, "MODDIR", str(self.mods_dir)):
            return data.load_civ(name)

    def ids(self):
        with mock.patch.object(data, "MODDIR", str(self.mods_dir)):
            return data.civilization_ids()

    def test_patch_changes_only_named_fields(self):
        base = self.load()
        self.add_mod("test_acme_k3f9", civs={"rome_100ad": rome_patch(
            population=7, values={"w_military": 0.9})})
        civ = self.load()
        self.assertEqual(7, civ["population"])
        self.assertEqual(0.9, civ["values"]["w_military"])
        self.assertEqual(base["values"]["w_commerce"], civ["values"]["w_commerce"])
        self.assertEqual(base["starting_techs"], civ["starting_techs"])
        self.assertEqual(base["name"], civ["name"])

    def test_patch_replaces_starting_techs(self):
        self.add_mod("test_acme_k3f9", civs={"rome_100ad": rome_patch(starting_techs=[])})
        self.assertEqual([], self.load()["starting_techs"])

    def test_patch_of_missing_civ_is_an_error(self):
        self.add_mod("test_acme_k3f9", civs={"nowhere_1ad": rome_patch(population=1)})
        with self.assertRaises(ModError):
            self.load("nowhere_1ad")

    def test_unrelated_mods_patching_same_field_name_both(self):
        for mod_id, population in (("test_acme_k3f9", 1), ("test_zeta_k3f9", 2)):
            self.add_mod(mod_id, civs={"rome_100ad": rome_patch(population=population)})
        with self.assertRaises(ModError) as caught:
            self.load()
        for word in ("test_acme_k3f9", "test_zeta_k3f9", "population"):
            self.assertIn(word, str(caught.exception))

    def test_dependent_patch_wins(self):
        self.add_mod("test_acme_k3f9", civs={"rome_100ad": rome_patch(population=1)})
        self.add_mod("test_zeta_k3f9", dependencies=["test_acme_k3f9"],
                     civs={"rome_100ad": rome_patch(population=2)})
        self.assertEqual(2, self.load()["population"])

    def test_hidden_civ_leaves_the_listing(self):
        self.assertIn("rome_100ad", self.ids())
        self.add_mod("test_acme_k3f9", civs={"rome_100ad": rome_patch(hidden=True)})
        self.assertNotIn("rome_100ad", self.ids())
        self.assertIn("han_china_100ad", self.ids())

    def test_hidden_civ_still_loads_by_name(self):
        self.add_mod("test_acme_k3f9", civs={"rome_100ad": rome_patch(hidden=True)})
        self.assertEqual("rome_100ad", self.load()["id"])

    def test_starting_tech_removed_by_mod_is_an_error(self):
        tech = self.load()["starting_techs"][0]
        self.add_mod("test_acme_k3f9", nodes=[{"id": tech, "remove": True}])
        with self.assertRaises(ModError) as caught:
            self.load()
        for word in (tech, "test_acme_k3f9", "rome_100ad"):
            self.assertIn(word, str(caught.exception))

    def test_starting_tech_removal_patched_away(self):
        base = self.load()
        tech = base["starting_techs"][0]
        kept = [item for item in base["starting_techs"] if item != tech]
        self.add_mod("test_acme_k3f9", nodes=[{"id": tech, "remove": True}],
                     civs={"rome_100ad": rome_patch(starting_techs=kept)})
        self.assertEqual(kept, self.load()["starting_techs"])

    def test_new_civ_is_still_added(self):
        self.add_mod("test_acme_k3f9", civs={"test_acme_k3f9:land": {"id": "test_acme_k3f9:land", "starting_techs": [],
                                       "starting_interest_rate": 0.1, "starting_tax_share": 0.05,
                                       "coin_standard": {"material": "silver_kg", "kg_per_unit": 0.003, "source": "test"}}})
        self.assertIn("test_acme_k3f9:land", self.ids())
        self.assertEqual("test_acme_k3f9:land", self.load("test_acme_k3f9:land")["id"])


if __name__ == "__main__":
    unittest.main()
