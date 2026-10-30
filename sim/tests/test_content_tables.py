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
