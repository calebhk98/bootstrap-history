"""Override semantics for goals (keyed by node) and trades in mod data."""
import copy
import json
import unittest

from sim.engine.catalog import load_production_catalog, load_trade_registry
from sim.engine.mods import ModError, load_mod_tree
from sim.tests.test_mod_removal_and_civs import BASE_TREE, ModTestBase


class GoalOverrideTests(ModTestBase):
    def goals(self):
        tree = load_mod_tree(copy.deepcopy(BASE_TREE), self.manifests())
        return {goal["node"]: goal for goal in tree["meta"]["goals"]}

    def test_override_changes_only_named_fields(self):
        self.add_mod("test_acme_k3f9", goals=[{"node": "c", "override": True, "name": "Renamed"}])
        goals = self.goals()
        self.assertEqual("Renamed", goals["c"]["name"])
        self.assertEqual("A", goals["a"]["name"])
        self.assertEqual(2, len(goals))

    def test_nested_null_deletes_a_key(self):
        base = copy.deepcopy(BASE_TREE)
        base["meta"]["goals"][0]["extra"] = {"keep": 1, "drop": 2}
        self.add_mod("test_acme_k3f9", goals=[{"node": "c", "override": True, "extra": {"drop": None}}])
        goal = {g["node"]: g for g in load_mod_tree(base, self.manifests())["meta"]["goals"]}["c"]
        self.assertEqual({"keep": 1}, goal["extra"])

    def test_override_of_missing_goal_is_an_error(self):
        self.add_mod("test_acme_k3f9", goals=[{"node": "d", "override": True, "name": "X"}])
        with self.assertRaises(ModError) as caught:
            self.goals()
        self.assertIn("d", str(caught.exception))

    def test_unrelated_mods_on_same_field_name_both(self):
        for mod_id in ("test_acme_k3f9", "test_zeta_k3f9"):
            self.add_mod(mod_id, goals=[{"node": "c", "override": True, "name": mod_id}])
        with self.assertRaises(ModError) as caught:
            self.goals()
        for word in ("test_acme_k3f9", "test_zeta_k3f9", "name", "c"):
            self.assertIn(word, str(caught.exception))

    def test_different_fields_merge(self):
        self.add_mod("test_acme_k3f9", goals=[{"node": "c", "override": True, "name": "N"}])
        self.add_mod("test_zeta_k3f9", goals=[{"node": "c", "override": True, "blurb": "B"}])
        goal = self.goals()["c"]
        self.assertEqual(("N", "B"), (goal["name"], goal["blurb"]))

    def test_dependent_mod_wins(self):
        self.add_mod("test_acme_k3f9", goals=[{"node": "c", "override": True, "name": "one"}])
        self.add_mod("test_zeta_k3f9", dependencies=["test_acme_k3f9"],
                     goals=[{"node": "c", "override": True, "name": "two"}])
        self.assertEqual("two", self.goals()["c"]["name"])

    def test_override_of_goal_removed_by_unrelated_mod_names_both(self):
        self.add_mod("test_acme_k3f9", goals=[{"node": "c", "remove": True}])
        self.add_mod("test_zeta_k3f9", goals=[{"node": "c", "override": True, "name": "X"}])
        with self.assertRaises(ModError) as caught:
            self.goals()
        for word in ("test_acme_k3f9", "test_zeta_k3f9"):
            self.assertIn(word, str(caught.exception))


class TradeOverrideTests(ModTestBase):
    def setUp(self):
        super().setUp()
        (self.root / "data/world").mkdir(parents=True)
        (self.root / "data/production").mkdir(parents=True)
        (self.root / "data/world/trades.json").write_text(json.dumps({"trades": {
            "smith": {"family": "craft", "note": "base note", "training": "apprentice"},
            "scribe": {"family": "scholar"}}}))
        (self.root / "data/production/base.json").write_text(json.dumps({"materials": {
            "ore": {"outputs": {"ore": 1}, "inputs": {}, "labour_hours": {"smith": 1}}}}))

    def registry(self):
        production = load_production_catalog(str(self.root), str(self.mods_dir),
                                             manifests=self.manifests())
        return load_trade_registry(str(self.root), production, str(self.mods_dir))

    def test_override_changes_only_named_fields(self):
        self.add_mod("test_acme_k3f9", trades={"smith": {"override": True, "note": "new"}})
        smith = self.registry()["smith"]
        self.assertEqual(("new", "craft", "apprentice"),
                         (smith.note, smith.family, smith.training))

    def test_override_of_missing_trade_is_an_error(self):
        self.add_mod("test_acme_k3f9", trades={"baker": {"override": True, "note": "x"}})
        with self.assertRaises(ModError) as caught:
            self.registry()
        self.assertIn("baker", str(caught.exception))

    def test_unrelated_mods_on_same_field_name_both(self):
        for mod_id in ("test_acme_k3f9", "test_zeta_k3f9"):
            self.add_mod(mod_id, trades={"smith": {"override": True, "note": mod_id}})
        with self.assertRaises(ModError) as caught:
            self.registry()
        for word in ("test_acme_k3f9", "test_zeta_k3f9", "note", "smith"):
            self.assertIn(word, str(caught.exception))

    def test_different_fields_merge(self):
        self.add_mod("test_acme_k3f9", trades={"smith": {"override": True, "note": "n"}})
        self.add_mod("test_zeta_k3f9", trades={"smith": {"override": True, "family": "scholar"}})
        smith = self.registry()["smith"]
        self.assertEqual(("n", "scholar"), (smith.note, smith.family))

    def test_dependent_mod_wins(self):
        self.add_mod("test_acme_k3f9", trades={"smith": {"override": True, "note": "one"}})
        self.add_mod("test_zeta_k3f9", dependencies=["test_acme_k3f9"],
                     trades={"smith": {"override": True, "note": "two"}})
        self.assertEqual("two", self.registry()["smith"].note)

    def test_override_of_trade_removed_by_unrelated_mod_names_both(self):
        self.add_mod("test_acme_k3f9", trades={"scribe": {"remove": True}})
        self.add_mod("test_zeta_k3f9", trades={"scribe": {"override": True, "note": "x"}})
        with self.assertRaises(ModError) as caught:
            self.registry()
        for word in ("test_acme_k3f9", "test_zeta_k3f9"):
            self.assertIn(word, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
