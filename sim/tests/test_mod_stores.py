"""Complaint 495: mods (and the base game) declare saved values per tile, per actor and per ordered actor pair.

Slow topic: it builds a game (not in the quick tier)."""
import json
import os
import tempfile
import unittest

from .harness import NODES, unopened_sim
from sim.engine import mod_code, mod_stores
from sim.engine.mods import ModError
from sim.engine.saveload import load_state, save_state
from sim.engine.year_phases import MOD_PHASES
from sim.ui.proto import mod_commands
from sim.ui.proto.dispatch import _agent_dispatch_inner
from sim.ui.proto.screen_map import map_screen
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


class StoreTests(StoreTestBase):
    def test_tile_store_written_in_a_phase_survives_a_save_and_a_read_command_returns_it(self):
        self.add_mod(ACME)
        self.write_data(ACME, "data/stores.json", MANA)
        mod_stores.load_mod_stores(str(self.mods_dir))
        game = unopened_sim()
        game.tile_owner_map()
        tile = sorted(game.tile_owner_map())[0]
        api = mod_code.ModCodeApi(ACME)

        def grow(sim, seats):
            api.write_store(sim, "mana", tile, sim.stores.view(ACME + ":mana").get(tile) + 2.5)
        api.phase("grow", "world", grow, after="market")
        self.assertIn(ACME + ":grow", [phase.name for phase in MOD_PHASES])
        grow(game, [])
        grow(game, [])
        self.assertEqual(game.stores.view(ACME + ":mana").get(tile), 5.0)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "save.json")
            save_state(game, path)
            revived = unopened_sim()
            load_state(revived, path)
        self.assertEqual(revived.stores.view(ACME + ":mana").get(tile), 5.0)
        self.assertEqual(revived.stores.view(ACME + ":mana").get("elsewhere"), 0.0)   # the default
        self.write_data(ACME, "data/ui/commands.json", {"commands": {ACME + ":mana": {
            "kind": "read", "summary": "mana", "description": "Mana on a tile.",
            "shows": [{"label": "Mana", "path": "stores.%s:mana.%s" % (ACME, tile), "unit": "mana", "digits": 1}]}}})
        mod_commands.load_mod_commands(str(self.mods_dir))
        reply = _agent_dispatch_inner(revived, NODES, {"cmd": ACME + ":mana"})
        self.assertEqual(reply["values"], [{"label": "Mana", "value": 5.0, "unit": "mana"}])

    def test_map_shows_a_tile_store_as_a_layer(self):
        self.add_mod(ACME)
        self.write_data(ACME, "data/stores.json", MANA)
        mod_stores.load_mod_stores(str(self.mods_dir))
        game = unopened_sim()
        base = game.labour.base_tile()
        game.stores.write(ACME + ":mana", base, 7.0)
        reply = map_screen(game, {"layer": ACME + ":mana"})
        self.assertEqual({row["tile"]: row["layer_value"] for row in reply["tiles"]}[base], 7.0)
        self.assertEqual(reply["layer"]["unit"], "mana")
        self.assertEqual(map_screen(game, {"layer": "nothing"})["cause"], "unknown_layer")
        self.assertEqual(map_screen(game, {"layer": "control"})["layer"]["store"], "control")

    def test_actor_pair_store_keys_by_the_ordered_pair(self):
        feud = mod_code.ModCodeApi(ACME).store("feud", keyed_by="actor_pair", default=0, unit="grievances")
        game = unopened_sim()
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
            mod_code.ModCodeApi(ACME).write_store(unopened_sim(), "ghost", "tile_1", 1)
        self.assertIn(ACME, str(caught.exception))

    def test_a_mod_cannot_write_another_mods_store(self):
        mod_code.ModCodeApi(ACME).store("mana", "tile", 0, "mana")
        with self.assertRaises(ModError) as caught:
            mod_code.ModCodeApi(BETA).write_store(unopened_sim(), ACME + ":mana", "tile_1", 1)
        self.assertIn(BETA, str(caught.exception))

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


class BaseControlTests(unittest.TestCase):
    def test_tile_control_is_the_base_game_control_store(self):
        game = unopened_sim()
        tile = sorted(game.tile_owner_map())[0]
        self.assertEqual(game.stores.view("control").get(tile), game.tile_control(tile))
        self.assertNotIn("control", game.tile_owner_map()[tile])
        game.transfer_tile(tile, "rival", "garrisoned")
        self.assertEqual(game.stores.control.get(tile), "garrisoned")
        game.transfer_tile(tile, None)
        self.assertIsNone(game.tile_control(tile))
        self.assertEqual(mod_stores.DECLARED["control"].owner, "")


if __name__ == "__main__":
    unittest.main()
