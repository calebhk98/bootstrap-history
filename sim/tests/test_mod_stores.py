"""Complaint 495: mods declare saved values per tile, per actor and per ordered actor pair: a store is declared once, in
the declaring mod's own namespace, and only its mod writes it. The declarations of a game are what its providers answered
(`declare_all`); the data files are read by `mod_stores`; the writes go through the stores module over a stub host. The stores as
the player and the base game reach them (read commands, the map, tile control) are in `test_mod_store_reads`."""

QUICK_TOPIC = True

import json
import unittest

from sim.engine import mod_code, mod_stores
from sim.content.api import ModError
from sim.engine.mod_effects import ModEffects
from sim.stores.api import StoreSpec, declare_all
from sim.tests.store_stand_in import StoreHost
from sim.tests.bridge_send import attach_send
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
        mod_code.LOADED.clear()
        mod_code.MOD_OPERATIONS.clear()

    def write_data(self, mod_id, relative, document):
        path = self.mods_dir / mod_id / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document))


def host_declaring(*specs):
    """A game with nothing but its stores, declared by one provider, and a `send` that applies a `WriteStore`."""
    return attach_send(StoreHost(*specs))


def declared_by_the_mod_door(mod_id, name, keyed_by="tile", default=0.0, unit="mana"):
    """The spec the mod door gives to the `store_declarations` point, and the handle it returns."""
    api = mod_code.ModCodeApi(mod_id)
    handle = api.store(name, keyed_by=keyed_by, default=default, unit=unit)
    (answer,) = api.operations.provided["store_declarations"]
    return answer(), handle


class StoreRules(StoreTestBase):
    def test_actor_pair_store_keys_by_the_ordered_pair(self):
        specs, feud = declared_by_the_mod_door(ACME, "feud", keyed_by="actor_pair", default=0, unit="grievances")
        game = host_declaring(*specs)
        feud.set(game, ("house_a", "house_b"), 3)
        self.assertEqual(feud.get(game, ("house_a", "house_b")), 3)
        self.assertEqual(feud.get(game, ("house_b", "house_a")), 0)
        self.assertEqual(feud.items(game), [("house_a|house_b", 3)])
        with self.assertRaises(ModError):
            feud.set(game, "house_a", 1)
        feud.set(game, ("house_a", "house_b"), 0)   # back to the default: nothing is kept
        self.assertEqual(game.stores_module.world.values[ACME + ":feud"], {})

    def test_undeclared_write_names_the_mod(self):
        with self.assertRaises(ModError) as caught:
            mod_code.ModCodeApi(ACME).write_store(host_declaring(), "ghost", "tile_1", 1)
        self.assertIn(ACME, str(caught.exception))

    def test_a_mod_cannot_write_another_mods_store(self):
        specs, _handle = declared_by_the_mod_door(ACME, "mana")
        host = host_declaring(*specs)
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
            declare_all([mod_stores.data_declarations(str(self.mods_dir))])

    def test_duplicate_between_code_and_data_is_a_load_error(self):
        self.add_mod(ACME)
        self.write_data(ACME, "data/stores.json", MANA)
        from_code, _handle = declared_by_the_mod_door(ACME, "mana", default=1.0)
        with self.assertRaises(ModError):
            declare_all([mod_stores.data_declarations(str(self.mods_dir)), from_code])

    def test_the_same_declaration_twice_is_one_store(self):
        spec = StoreSpec(ACME + ":mana", ACME, "tile", 0.0, "mana")
        self.assertEqual(declare_all([[spec], [spec]]), {spec.name: spec})

    def test_a_name_outside_the_mods_namespace_is_refused(self):
        self.add_mod(ACME)
        self.write_data(ACME, "data/stores.json", {"stores": {"mana": {"keyed_by": "tile", "default": 0, "unit": ""}}})
        with self.assertRaises(ModError):
            mod_stores.data_declarations(str(self.mods_dir))

    def test_a_store_keyed_by_nothing_known_is_refused_where_the_mod_declares_it(self):
        with self.assertRaises(ModError):
            mod_code.ModCodeApi(ACME).store("mana", "region", 0, "mana")

    def test_the_data_declarations_come_in_mod_load_order_with_their_owner(self):
        self.add_mod(ACME)
        self.write_data(ACME, "data/stores.json", MANA)
        (spec,) = mod_stores.data_declarations(str(self.mods_dir))
        self.assertEqual((spec.name, spec.owner, spec.keyed_by), (ACME + ":mana", ACME, "tile"))

    def test_the_base_game_declares_control_as_a_tile_store_with_no_owning_mod(self):
        declared = {spec.name: spec for spec in mod_stores.base_declarations()}
        self.assertEqual((declared["control"].owner, declared["control"].keyed_by), ("", "tile"))


if __name__ == "__main__":
    unittest.main()
