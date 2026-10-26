"""Complaint 495: mods declare saved values per tile, per actor and per ordered actor pair: a store is declared once, in
the declaring mod's own namespace, and only its mod writes it. Called on a stub host over the real `ModStoresMixin`; the
stores as the player and the base game reach them (read commands, the map, tile control) are in `test_mod_store_reads`."""

QUICK_TOPIC = True

import json
import unittest
from types import SimpleNamespace

from sim.engine import mod_code, mod_stores
from sim.engine.mods import ModError
from sim.tests.bridge_send import attach_send
from sim.engine.mod_effects import ModEffects
from sim.engine.mod_stores import ModStoresMixin
from sim.engine.year_phases import MOD_PHASES
from sim.ui.proto import mod_commands
from sim.tests.test_mod_removal_and_civs import ModTestBase

ACME = "test_acme_k3f9"
BETA = "test_beta_k3f9"
MANA = {"stores": {ACME + ":mana": {"keyed_by": "tile", "default": 0.0, "unit": "mana"}}}


class StoreTestBase(ModTestBase):
    def setUp(self):
        super().setUp()
        self.clean()

    def tearDown(self):
        self.clean()
        super().tearDown()

    def clean(self):
        mod_stores.forget_mod_stores()
        mod_code.LOADED.clear()
        mod_code.COMMAND_REGISTRATIONS.clear()
        mod_commands.forget_mod_commands()
        MOD_PHASES.clear()

    def write_data(self, mod_id, relative, document):
        path = self.mods_dir / mod_id / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document))


class Host(ModStoresMixin):
    """A game with nothing but its saved stores."""

    def __init__(self):
        self.state = SimpleNamespace(stores={})
        attach_send(self)


class StoreRules(StoreTestBase):
    def test_actor_pair_store_keys_by_the_ordered_pair(self):
        feud = mod_code.ModCodeApi(ACME).store("feud", keyed_by="actor_pair", default=0, unit="grievances")
        game = Host()
        feud.set(game, ("house_a", "house_b"), 3)
        self.assertEqual(feud.get(game, ("house_a", "house_b")), 3)
        self.assertEqual(feud.get(game, ("house_b", "house_a")), 0)
        self.assertEqual(feud.items(game), [("house_a|house_b", 3)])
        with self.assertRaises(ModError):
            feud.set(game, "house_a", 1)
        feud.set(game, ("house_a", "house_b"), 0)   # back to the default: nothing is kept
        self.assertEqual(game.state.stores[ACME + ":feud"], {})

    def test_undeclared_write_names_the_mod(self):
        with self.assertRaises(ModError) as caught:
            mod_code.ModCodeApi(ACME).write_store(Host(), "ghost", "tile_1", 1)
        self.assertIn(ACME, str(caught.exception))

    def test_a_mod_cannot_write_another_mods_store(self):
        mod_code.ModCodeApi(ACME).store("mana", "tile", 0, "mana")
        host = Host()
        with self.assertRaises(ModError) as caught:
            ModEffects(BETA).write_store(host, ACME + ":mana", "tile_1", 1)
        self.assertIn(BETA, str(caught.exception))
        self.assertIn(ACME, str(caught.exception))
        self.assertEqual(host.stores.view(ACME + ":mana").values, {})
        ModEffects(ACME).write_store(host, ACME + ":mana", "tile_1", 1)
        self.assertEqual(host.stores.view(ACME + ":mana").get("tile_1"), 1)

    def test_duplicate_declaration_across_two_mods_is_a_load_error(self):
        for mod_id in (ACME, BETA):
            self.add_mod(mod_id)
        self.write_data(ACME, "data/stores.json", MANA)
        self.write_data(BETA, "data/stores.json", {"stores": {ACME + ":mana": MANA["stores"][ACME + ":mana"]}})
        with self.assertRaises(ModError):
            mod_stores.load_mod_stores(str(self.mods_dir))

    def test_duplicate_between_code_and_data_is_a_load_error(self):
        self.add_mod(ACME)
        self.write_data(ACME, "data/stores.json", MANA)
        mod_code.ModCodeApi(ACME).store("mana", "tile", 1.0, "mana")
        with self.assertRaises(ModError):
            mod_stores.load_mod_stores(str(self.mods_dir))

    def test_a_name_outside_the_mods_namespace_is_refused(self):
        self.add_mod(ACME)
        self.write_data(ACME, "data/stores.json", {"stores": {"mana": {"keyed_by": "tile", "default": 0, "unit": ""}}})
        with self.assertRaises(ModError):
            mod_stores.load_mod_stores(str(self.mods_dir))


if __name__ == "__main__":
    unittest.main()
