"""Complaint 840: every table a game reads from data (the tree's names, production, trades, technology effects, unit words, topic
tags, kits) is a function of the mods directory the game is over, so a temporary directory with one mod and an empty one give two
different tables through the main seams, in one process. No game is built."""
QUICK_TOPIC = True

import json
import os
import shutil
import tempfile
import unittest

from sim.content.api import load_tech_effects, trade_registry
from sim.engine import data, topic_tags, units
from sim.prices import prices
from sim.ui.proto import nodes
from sim.world import demand

MOD = "table_probe_q7r2"


def write(path, document):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        json.dump(document, handle)


class TablesFollowTheDirectory(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.with_mod = os.path.join(self.root, "with_mod")
        self.without_mod = os.path.join(self.root, "without_mod")
        os.makedirs(self.without_mod)
        base = os.path.join(self.with_mod, MOD)
        write(os.path.join(base, "mod.json"), {"id": MOD, "name": MOD, "version": "1", "dependencies": [], "conflicts": []})
        write(os.path.join(base, "data", "branches", "probe.json"),
              {"nodes": [{"id": MOD + ":probe_node", "name": "Probe technique", "mat": {}, "lab": {}, "pre": [], "cap_hours": 0}]})
        write(os.path.join(base, "data", "production", "probe.json"),
              {"materials": {MOD + ":gizmo": {"outputs": {MOD + ":gizmo": 1.0}, "labour_hours": {"labourer": 1.0}, "requires_node": None}}})
        write(os.path.join(base, "data", "world", "trades.json"), {"trades": {MOD + ":scribe": {"family": "scholar"}}})
        write(os.path.join(base, "data", "civilizations", "_TECH_EFFECTS.json"), {MOD + ":spark": {"w_magic_fear": 0.2}})
        write(os.path.join(base, "data", "world", "topic_tags.json"), {"tags": {MOD + ":probing": {"cats": ["probe"], "words": ["probe"]}}})
        write(os.path.join(base, "data", "world", "units.json"),
              {"units": {MOD + ":pr_unit": {"dimension": "mass", "factor": 1.0, "label": "pr"}}})

    def test_the_tree_names_differ(self):
        self.assertIn(MOD + ":probe_node", data.node_names(self.with_mod))
        self.assertNotIn(MOD + ":probe_node", data.node_names(self.without_mod))

    def test_the_typed_input_name_index_differs(self):
        self.assertIn(MOD + ":probe_node", nodes.names_for(self.with_mod).ids)
        self.assertNotIn(MOD + ":probe_node", nodes.names_for(self.without_mod).ids)
        self.assertEqual(nodes.names_for(self.with_mod).by_name["probe technique"], [MOD + ":probe_node"])

    def test_the_production_catalogue_differs(self):
        self.assertIn(MOD + ":gizmo", demand.production_data(self.with_mod))
        self.assertNotIn(MOD + ":gizmo", demand.production_data(self.without_mod))
        self.assertIs(prices.default_production_entries(self.with_mod), demand.production_data(self.with_mod))

    def test_the_trades_and_technology_effects_differ(self):
        self.assertIn(MOD + ":scribe", trade_registry(self.with_mod))
        self.assertNotIn(MOD + ":scribe", trade_registry(self.without_mod))
        self.assertIn(MOD + ":spark", load_tech_effects(self.with_mod))
        self.assertNotIn(MOD + ":spark", load_tech_effects(self.without_mod))

    def test_the_topic_tags_and_unit_words_differ(self):
        self.assertIn(MOD + ":probing", topic_tags.current(self.with_mod))
        self.assertNotIn(MOD + ":probing", topic_tags.current(self.without_mod))
        self.assertIn(MOD + ":pr_unit", units.registry(self.with_mod)["units"])
        self.assertNotIn(MOD + ":pr_unit", units.registry(self.without_mod)["units"])

    def test_the_wage_schedule_helpers_follow_the_directory(self):
        with_mod = data.schedule_of_civilisation(data.load_civ(mods_dir=self.with_mod), self.with_mod)
        without_mod = data.schedule_of_civilisation(data.load_civ(mods_dir=self.without_mod), self.without_mod)
        self.assertIn(MOD + ":scribe", with_mod.wages_per_hour())
        self.assertNotIn(MOD + ":scribe", without_mod.wages_per_hour())


if __name__ == "__main__":
    unittest.main()
