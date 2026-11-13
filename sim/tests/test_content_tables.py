"""The static tables the content package loads from files (sim/content/trades.py, tech_effects.py, foreign_economies.py): each is a
plain function of the directory and files it is handed."""

QUICK_TOPIC = True

import json
import os
import shutil
import tempfile
import unittest

from sim.content import foreign_economies, tech_effects, trades
from sim.content.api import OpenContent, Trade
from sim.content.directory_stamp import DirectoryMemo
from sim.content.module import Content

MOD = "test_tables_a1b2"


def write_json(path, document):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        json.dump(document, handle)


def write_mod(directory, document_by_relative_path):
    write_json(os.path.join(directory, MOD, "mod.json"),
               {"id": MOD, "name": MOD, "version": "1.0.0", "dependencies": [], "conflicts": []})
    for relative, document in document_by_relative_path.items():
        write_json(os.path.join(directory, MOD, relative), document)


REGISTRY = {"smith": Trade("smith", family="craft", note="hammers", initially_absent=False),
            "engineer": Trade("engineer", family="scholar", note="needs teaching", initially_absent=True)}


class TradeFactTests(unittest.TestCase):
    def test_notes_are_each_trades_note(self):
        self.assertEqual(trades.trade_notes(REGISTRY), {"smith": "hammers", "engineer": "needs teaching"})

    def test_absent_trades_are_those_flagged_initially_absent(self):
        self.assertEqual(trades.trades_absent(REGISTRY), frozenset({"engineer"}))

    def test_family_of_a_named_trade_is_its_family(self):
        self.assertEqual(trades.trade_family(REGISTRY, "engineer"), "scholar")

    def test_a_trade_the_registry_does_not_name_is_a_craft(self):
        self.assertEqual(trades.trade_family(REGISTRY, "unlisted"), "craft")


class TechEffectsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_underscore_keys_are_notes_and_dropped(self):
        path = os.path.join(self.directory, "effects.json")
        write_json(path, {"_note": "text", "press": {"w_magic_fear": -0.1}})
        self.assertEqual(tech_effects.load_tech_effects(os.path.join(self.directory, "none"), path),
                         {"press": {"w_magic_fear": -0.1}})

    def test_a_missing_file_is_an_empty_table(self):
        self.assertEqual(tech_effects.load_tech_effects(os.path.join(self.directory, "none"),
                                                        os.path.join(self.directory, "absent.json")), {})

    def test_a_mod_adds_its_own_node(self):
        path = os.path.join(self.directory, "effects.json")
        write_json(path, {"press": {"w_magic_fear": -0.1}})
        mods = os.path.join(self.directory, "mods")
        write_mod(mods, {os.path.join("data", "civilizations", "_TECH_EFFECTS.json"): {MOD + ":spark": {"w_magic_fear": 0.2}}})
        loaded = tech_effects.load_tech_effects(mods, path)
        self.assertEqual(set(loaded), {MOD + ":spark", "press"})


class TwoDirectoriesTwoTables(unittest.TestCase):
    """Complaint 840: the trade registry and the technology effects are functions of the mods directory a game holds, so two
    directories in one process give two tables (no import-time table stands for both)."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.with_mod = os.path.join(self.root, "with_mod")
        self.without_mod = os.path.join(self.root, "without_mod")
        os.makedirs(self.without_mod)
        write_mod(self.with_mod, {os.path.join("data", "world", "trades.json"): {"trades": {MOD + ":scribe": {"family": "scholar", "note": "writes"}}},
                                  os.path.join("data", "civilizations", "_TECH_EFFECTS.json"): {MOD + ":spark": {"w_magic_fear": 0.2}}})

    def test_the_trade_registries_of_two_directories_differ_by_the_mods_trade(self):
        with_mod = trades.trade_registry(self.with_mod)
        without_mod = trades.trade_registry(self.without_mod)
        self.assertEqual(set(with_mod) - set(without_mod), {MOD + ":scribe"})
        self.assertEqual(trades.trade_family(with_mod, MOD + ":scribe"), "scholar")
        self.assertEqual(trades.trade_notes(with_mod)[MOD + ":scribe"], "writes")

    def test_the_tech_effects_of_two_directories_differ_by_the_mods_node(self):
        with_mod = tech_effects.load_tech_effects(self.with_mod)
        without_mod = tech_effects.load_tech_effects(self.without_mod)
        self.assertEqual(set(with_mod) - set(without_mod), {MOD + ":spark"})
        self.assertEqual(set(without_mod) - set(with_mod), set())

    def test_a_directory_is_built_once_until_a_file_under_it_changes(self):
        builds = []
        memo = DirectoryMemo()
        self.assertEqual(memo.get(self.with_mod, lambda: builds.append(1) or "first"), "first")
        self.assertEqual(memo.get(self.with_mod, lambda: builds.append(1) or "again"), "first")
        self.assertEqual(len(builds), 1)
        write_json(os.path.join(self.with_mod, MOD, "extra.json"), {"changed": True})
        self.assertEqual(memo.get(self.with_mod, lambda: builds.append(1) or "second"), "second")
        self.assertEqual(memo.get(self.without_mod, lambda: builds.append(1) or "other"), "other")

    def test_a_changed_trade_file_gives_a_new_registry(self):
        self.assertEqual(trades.trade_notes(trades.trade_registry(self.with_mod))[MOD + ":scribe"], "writes")
        write_json(os.path.join(self.with_mod, MOD, "data", "world", "trades.json"),
                   {"trades": {MOD + ":scribe": {"family": "scholar", "note": "copies books"}}})
        self.assertEqual(trades.trade_notes(trades.trade_registry(self.with_mod))[MOD + ":scribe"], "copies books")

    def test_a_caller_changing_its_table_does_not_change_the_next_ones(self):
        trades.trade_registry(self.with_mod).clear()
        self.assertIn(MOD + ":scribe", trades.trade_registry(self.with_mod))
        tech_effects.load_tech_effects(self.with_mod)[MOD + ":spark"]["w_magic_fear"] = 9.0
        self.assertEqual(tech_effects.load_tech_effects(self.with_mod)[MOD + ":spark"]["w_magic_fear"], 0.2)

    def test_two_directories_give_two_production_catalogues(self):
        from sim.prices import prices
        write_json(os.path.join(self.with_mod, MOD, "data", "production", "extra.json"),
                   {"materials": {MOD + ":gizmo": {"outputs": {MOD + ":gizmo": 1.0}, "labour_hours": {"labourer": 1.0}}}})
        with_mod = prices.default_production_entries(self.with_mod)
        without_mod = prices.default_production_entries(self.without_mod)
        self.assertEqual(set(with_mod) - set(without_mod), {MOD + ":gizmo"})
        self.assertIs(prices.default_production_entries(self.with_mod), with_mod)


class ForeignEconomyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.path = os.path.join(self.directory, "foreign_economies.json")
        write_json(self.path, {"economies": [{"civilization": "han"}], "not_traded_materials": ["salt"]})

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_without_mods_the_file_is_the_document(self):
        document = foreign_economies.foreign_economy_document(os.path.join(self.directory, "none"), self.path)
        self.assertEqual(document["economies"], [{"civilization": "han"}])
        self.assertEqual(document["not_traded_materials"], ["salt"])

    def test_a_mods_untraded_materials_join_the_base_ones_sorted(self):
        mods = os.path.join(self.directory, "mods")
        write_mod(mods, {os.path.join("data", "world", "foreign_economies.json"): {"not_traded_materials": [MOD + ":relic"]}})
        document = foreign_economies.foreign_economy_document(mods, self.path)
        self.assertEqual(document["not_traded_materials"], sorted(["salt", MOD + ":relic"]))


class ContentModuleTableTests(unittest.TestCase):
    def opened(self):
        content = Content()
        content.setup()
        content.open_content(OpenContent(""))
        return content

    def test_the_trade_records_are_read_once_for_a_directory(self):
        content = self.opened()
        self.assertIs(content.trade_records(), content.trade_records())

    def test_the_family_view_reads_the_registry(self):
        content = self.opened()
        trade = next(iter(content.trade_records()))
        self.assertEqual(content.trade_family(trade), content.trade_records()[trade].family)


if __name__ == "__main__":
    unittest.main()
