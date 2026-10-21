"""SCENARIO: in a game a mod's tile store written in a phase survives a save and answers a read command, the map shows it
as a layer, and tile control is the base game's control store (Complaint 495). The declaration rules are in
`test_mod_stores`."""
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
from sim.tests.test_mod_stores import StoreTestBase

ACME = "test_acme_k3f9"
BETA = "test_beta_k3f9"
MANA = {"stores": {ACME + ":mana": {"keyed_by": "tile", "default": 0.0, "unit": "mana"}}}


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
