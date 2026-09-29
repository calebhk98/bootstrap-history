"""Acceptance tests for third-party economic content with no base-data edits."""
import json
from pathlib import Path
import tempfile
import unittest

from sim.engine.catalog import (load_production_catalog, load_trade_registry,
                                material_namespace, transitional_wage_rates,
                                validate_mod_material_paths)
from sim.engine.mods import get_ordered_mods, load_mod_tree
from sim.engine import prices
from sim.validate_production import check
from sim.world import demand, labour_market


class ModEconomicCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data/production").mkdir(parents=True)
        (self.root / "data/production/base.json").write_text('{"materials": {}}')
        mod = self.root / "mods/test_acme_k3f9"
        (mod / "data/production").mkdir(parents=True)
        (mod / "data/branches").mkdir(parents=True)
        (mod / "data/civilizations").mkdir(parents=True)
        (mod / "data/world").mkdir(parents=True)
        (mod / "mod.json").write_text(json.dumps({
            "id": "test_acme_k3f9", "name": "Acme", "version": "1", "dependencies": [], "conflicts": []}))
        self.nodes = [{"id": "test_acme_k3f9:metallurgy", "name": "Metallurgy", "mat": {"test_acme_k3f9:ingot": 10},
                       "lab": {}, "pre": [], "cap": 0}]
        (mod / "data/branches/metals.json").write_text(json.dumps({"nodes": self.nodes}))
        (mod / "data/goals.json").write_text(json.dumps({"goals": [{"id": "test_acme_k3f9:goal", "node": "test_acme_k3f9:metallurgy"}]}))
        (mod / "data/civilizations/test_acme_k3f9+republic.json").write_text(json.dumps({
            "id": "test_acme_k3f9:republic", "starting_techs": [], "start_year": 1}))
        (mod / "data/world/trades.json").write_text(json.dumps({
            "trades": {"test_acme_k3f9:clockmaker": {
                "family": "craft", "training": "apprenticeship",
                "initially_absent": True,
                "note": "Must be established before clockmakers can be hired."}}}))
        self.production = {
            "test_acme_k3f9:ore": {"outputs": {"test_acme_k3f9:ore": 1}, "inputs": {},
                         "labour_hours": {"labourer": 2}, "extracted_from": "deposit",
                         "requires_node": None, "yield_basis": "Synthetic acceptance-test extraction basis with explicit unit output.", "conf": "C"},
            "test_acme_k3f9:ingot": {"outputs": {"test_acme_k3f9:ingot": 1}, "inputs": {"test_acme_k3f9:ore": 2},
                           "labour_hours": {"test_acme_k3f9:clockmaker": 1},
                           "requires_node": None, "yield_basis": "Synthetic acceptance-test smelting basis with explicit mass conversion.", "conf": "C"}}
        (mod / "data/production/metals.json").write_text(json.dumps({"materials": self.production}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_generic_civilization_goal_and_technology(self):
        manifests = get_ordered_mods(str(self.root / "mods"))
        tree = load_mod_tree({"nodes": [], "meta": {"goals": []}}, manifests)
        self.assertEqual(["test_acme_k3f9"], [mod.id for mod in manifests])
        self.assertTrue((self.root / "mods/test_acme_k3f9/data/civilizations/test_acme_k3f9+republic.json").is_file())
        self.assertIn("test_acme_k3f9:metallurgy", {node["id"] for node in tree["nodes"]})
        self.assertIn("test_acme_k3f9:goal", {goal["id"] for goal in tree["meta"]["goals"]})

    def test_new_material_chain_is_solved_and_visible_everywhere(self):
        production = load_production_catalog(str(self.root), str(self.root / "mods"))
        self.assertIn("test_acme_k3f9:ingot", material_namespace(production, self.nodes))
        price_book = {"wage_rates_denarii_per_hour": {"labourer": {"rate": 1.0}}}
        solved = prices.solved_prices([], price_book, production_entries=production)
        self.assertIn("test_acme_k3f9:ingot", solved.resolvable_materials)
        goods, provenance = prices.priced_goods_table([], {}, price_book, production_entries=production)
        self.assertGreater(goods["test_acme_k3f9:ingot"], 0)
        self.assertEqual("solved", provenance["test_acme_k3f9:ingot"])
        self.assertEqual(10 * goods["test_acme_k3f9:ingot"],
                         sum(goods[m] * q for m, q in self.nodes[0]["mat"].items()))
        self.assertIs(production, load_production_catalog(str(self.root), str(self.root / "mods")))
        self.assertEqual(4, demand.derived_intermediate_demand("test_acme_k3f9:ore", {"test_acme_k3f9:ingot": 2}, production)[0])
        need, _breakdown = labour_market.labour_hours_required_by_trade({"test_acme_k3f9:ingot": 2}, production)
        self.assertEqual(2, need["test_acme_k3f9:clockmaker"])
        self.assertFalse(check(production, material_namespace(production),
                               set(load_trade_registry(str(self.root), production,
                                                       str(self.root / "mods")))))

    def test_broken_mod_material_has_actionable_error_shape(self):
        material = "test_acme_k3f9:nonexistent_material"
        manifests = get_ordered_mods(str(self.root / "mods"))
        with self.assertRaises(ValueError) as caught:
            validate_mod_material_paths(
                [{"id": "test_acme_k3f9:broken", "mat": {material: 1}}],
                load_production_catalog(str(self.root), str(self.root / "mods")), manifests)
        message = str(caught.exception)
        self.assertIn("test_acme_k3f9:broken", message)
        self.assertIn(material, message)
        self.assertIn("no production recipe", message)

    def test_new_trade_identity_does_not_require_static_wage(self):
        registry = load_trade_registry(str(self.root), mods_dir=str(self.root / "mods"))
        self.assertIn("test_acme_k3f9:clockmaker", registry)
        self.assertTrue(registry["test_acme_k3f9:clockmaker"].initially_absent)
        self.assertIn("established", registry["test_acme_k3f9:clockmaker"].note)
        self.assertNotIn("test_acme_k3f9:clockmaker", {"labourer": 1.0})
        rates = transitional_wage_rates(registry, {"labourer": 1.0})
        self.assertGreater(rates["test_acme_k3f9:clockmaker"], 0)

    def test_base_trade_registry_owns_identity_and_availability(self):
        repo = Path(__file__).resolve().parents[2]
        registry = load_trade_registry(str(repo), mods_dir=str(repo / "mods"))
        price_book = json.loads((repo / "data/prices.json").read_text())
        calibrated = {trade for trade in price_book["wage_rates_denarii_per_hour"]
                      if not trade.startswith("_")}
        self.assertEqual(calibrated, set(registry))
        self.assertEqual(
            {"chemist", "electrician", "engineer", "machinist", "optician"},
            {trade.id for trade in registry.values() if trade.initially_absent})
        self.assertIn("private one is your invention", registry["engineer"].note)

    def test_bundled_mods_load_generically(self):
        repo = Path(__file__).resolve().parents[2]
        manifests = get_ordered_mods(str(repo / "mods"))
        ids = {mod.id for mod in manifests}
        self.assertIn("sample_egypt_100bc_e7k2", ids)
        self.assertIn("sample_slaveholding_goal_m4q8", ids)
        base = json.loads((repo / "data/tech_tree.json").read_text())
        tree = load_mod_tree(base, manifests)
        self.assertTrue(any(goal.get("node", "").startswith("sample_slaveholding_goal_m4q8:")
                            for goal in tree["meta"]["goals"]))


if __name__ == "__main__":
    unittest.main()
