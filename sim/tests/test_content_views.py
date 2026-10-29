"""What the mods installed in one directory contribute (sim/content/views.py): each view is a plain function of the directory,
and the content module answers with the directory it was given."""

QUICK_TOPIC = True

import json
import os
import shutil
import tempfile
import unittest

from sim.content import views
from sim.content.api import OpenContent
from sim.content.module import Content

FIRST = "test_first_a1b2"
SECOND = "test_second_c3d4"


def write_mod(directory, mod_id, dependencies=()):
    os.makedirs(os.path.join(directory, mod_id))
    manifest = {"id": mod_id, "name": mod_id, "version": "1.0.0", "dependencies": list(dependencies), "conflicts": []}
    with open(os.path.join(directory, mod_id, "mod.json"), "w") as handle:
        json.dump(manifest, handle)


def write_data(directory, mod_id, relative, document):
    path = os.path.join(directory, mod_id, relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        json.dump(document, handle)


class ContentViewTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_installed_mod_ids_follow_dependency_order(self):
        write_mod(self.directory, FIRST, dependencies=[SECOND])
        write_mod(self.directory, SECOND)
        self.assertEqual(views.installed_mod_ids(self.directory), (SECOND, FIRST))

    def test_an_empty_directory_installs_nothing(self):
        self.assertEqual(views.installed_mod_ids(self.directory), ())
        self.assertEqual(views.map_overlays(self.directory), [])
        self.assertEqual(views.data_store_declarations(self.directory), [])

    def test_map_overlays_pair_each_mod_with_its_directory(self):
        write_mod(self.directory, FIRST)
        overlays = views.map_overlays(self.directory)
        self.assertEqual([mod_id for mod_id, _ in overlays], [FIRST])
        self.assertEqual(os.path.realpath(overlays[0][1]), os.path.realpath(os.path.join(self.directory, FIRST)))

    def test_data_store_declarations_name_their_mod(self):
        write_mod(self.directory, FIRST)
        write_data(self.directory, FIRST, os.path.join("data", "stores.json"),
                   {"stores": {FIRST + ":mana": {"keyed_by": "tile", "default": 0.0, "unit": "mana"}}})
        (spec,) = views.data_store_declarations(self.directory)
        self.assertEqual((spec.name, spec.owner, spec.keyed_by), (FIRST + ":mana", FIRST, "tile"))

    def test_household_need_data_adds_the_mods_needs_to_the_base(self):
        base = views.household_need_data(os.path.join(self.directory, "absent"))
        write_mod(self.directory, FIRST)
        write_data(self.directory, FIRST, os.path.join("data", "world", "needs.json"),
                   {"needs": {FIRST + ":cheer": {"surplus_budget_share": 0.01}}})
        loaded = views.household_need_data(self.directory)
        self.assertEqual(set(loaded["needs"]) - set(base["needs"]), {FIRST + ":cheer"})
        self.assertEqual(loaded["goods"], base["goods"])

    def test_declared_actor_kinds_are_the_mods_kinds(self):
        write_mod(self.directory, FIRST)
        declaration = {"needs": {"food": 1.0}, "birth_rate": 0.04, "death_rate": 0.02, "famine_death_rate": 0.3,
                       "trade": "labourer"}
        write_data(self.directory, FIRST, os.path.join("data", "world", "actor_kinds.json"),
                   {"kinds": {FIRST + ":elf": declaration}})
        self.assertEqual(list(views.declared_actor_kinds(self.directory)), [FIRST + ":elf"])


class ContentModuleTests(unittest.TestCase):
    def test_the_directory_is_the_one_opened(self):
        content = Content()
        content.open_content(OpenContent("/some/mods"))
        self.assertEqual(content.mods_directory(), "/some/mods")

    def test_an_unopened_module_has_no_mods(self):
        content = Content()
        self.assertEqual(content.installed_mod_ids(), ())
        self.assertEqual(content.map_overlays(), [])
        self.assertEqual(content.data_store_declarations(), [])


if __name__ == "__main__":
    unittest.main()
