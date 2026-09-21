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
        mod = self.root / "mods/acme"
        (mod / "data/production").mkdir(parents=True)
        (mod / "data/branches").mkdir(parents=True)
        (mod / "data/civilizations").mkdir(parents=True)
        (mod / "data/world").mkdir(parents=True)
        (mod / "mod.json").write_text(json.dumps({
            "id": "acme", "name": "Acme", "version": "1", "dependencies": [], "conflicts": []}))
        self.nodes = [{"id": "acme_metallurgy", "mat": {"acme_ingot": 10},
                       "lab": {}, "pre": [], "cap": 0}]
        (mod / "data/branches/metals.json").write_text(json.dumps({"nodes": self.nodes}))
        (mod / "data/goals.json").write_text(json.dumps({"goals": [{"id": "acme_goal", "node": "acme_metallurgy"}]}))
        (mod / "data/civilizations/acme_republic.json").write_text(json.dumps({
            "id": "acme_republic", "starting_techs": [], "start_year": 1}))
        (mod / "data/world/trades.json").write_text(json.dumps({
            "trades": {"acme_clockmaker": {"family": "craft", "training": "apprenticeship"}}}))
        self.production = {
            "acme_ore": {"outputs": {"acme_ore": 1}, "inputs": {},
                         "labour_hours": {"labourer": 2}, "extracted_from": "deposit",
                         "requires_node": None, "yield_basis": "Synthetic acceptance-test extraction basis with explicit unit output.", "conf": "C"},
            "acme_ingot": {"outputs": {"acme_ingot": 1}, "inputs": {"acme_ore": 2},
                           "labour_hours": {"acme_clockmaker": 1},
                           "requires_node": None, "yield_basis": "Synthetic acceptance-test smelting basis with explicit mass conversion.", "conf": "C"}}
        (mod / "data/production/metals.json").write_text(json.dumps({"materials": self.production}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_generic_civilization_goal_and_technology(self):
        manifests = get_ordered_mods(str(self.root / "mods"))
        tree = load_mod_tree({"nodes": [], "meta": {"goals": []}}, manifests)
        self.assertEqual(["acme"], [mod.id for mod in manifests])
        self.assertTrue((self.root / "mods/acme/data/civilizations/acme_republic.json").is_file())
        self.assertIn("acme_metallurgy", {node["id"] for node in tree["nodes"]})
        self.assertIn("acme_goal", {goal["id"] for goal in tree["meta"]["goals"]})

    def test_new_material_chain_is_solved_and_visible_everywhere(self):
        production = load_production_catalog(str(self.root), str(self.root / "mods"))
        self.assertIn("acme_ingot", material_namespace(production, self.nodes))
        price_book = {"wage_rates_denarii_per_hour": {"labourer": {"rate": 1.0}}}
        solved = prices.solved_prices([], price_book, production_entries=production)
        self.assertIn("acme_ingot", solved.resolvable_materials)
        goods, provenance = prices.priced_goods_table([], {}, price_book, production_entries=production)
        self.assertGreater(goods["acme_ingot"], 0)
        self.assertEqual("solved", provenance["acme_ingot"])
        self.assertEqual(10 * goods["acme_ingot"],
                         sum(goods[m] * q for m, q in self.nodes[0]["mat"].items()))
        self.assertIs(production, load_production_catalog(str(self.root), str(self.root / "mods")))
        self.assertEqual(4, demand.derived_intermediate_demand("acme_ore", {"acme_ingot": 2}, production)[0])
        need, _breakdown = labour_market.labour_hours_required_by_trade({"acme_ingot": 2}, production)
        self.assertEqual(2, need["acme_clockmaker"])
        self.assertFalse(check(production, material_namespace(production),
                               set(load_trade_registry(str(self.root), production,
                                                       str(self.root / "mods")))))

    def test_broken_mod_material_has_actionable_error_shape(self):
        material = "acme_nonexistent_material"
        manifests = get_ordered_mods(str(self.root / "mods"))
        with self.assertRaises(ValueError) as caught:
            validate_mod_material_paths(
                [{"id": "acme_broken", "mat": {material: 1}}],
                load_production_catalog(str(self.root), str(self.root / "mods")), manifests)
        message = str(caught.exception)
        self.assertIn("acme_broken", message)
        self.assertIn(material, message)
        self.assertIn("no production recipe", message)

    def test_new_trade_identity_does_not_require_static_wage(self):
        registry = load_trade_registry(str(self.root), mods_dir=str(self.root / "mods"))
        self.assertIn("acme_clockmaker", registry)
        self.assertNotIn("acme_clockmaker", {"labourer": 1.0})
        rates = transitional_wage_rates(registry, {"labourer": 1.0})
        self.assertGreater(rates["acme_clockmaker"], 0)

    def test_bundled_mods_load_generically(self):
        repo = Path(__file__).resolve().parents[2]
        manifests = get_ordered_mods(str(repo / "mods"))
        ids = {mod.id for mod in manifests}
        self.assertIn("egypt_100bc", ids)
        self.assertIn("slaveholding_goal", ids)
        base = json.loads((repo / "data/tech_tree.json").read_text())
        tree = load_mod_tree(base, manifests)
        self.assertTrue(any(goal.get("node", "").startswith("slaveholding_goal_")
                            for goal in tree["meta"]["goals"]))


if __name__ == "__main__":
    unittest.main()
