"""Mod ids are unique and namespaced: `<mod_id>:<name>`, mod ids `<author>_<name>_<suffix>`."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from sim.engine.mods import ModError, get_ordered_mods, load_mod_production, load_mod_tree
from sim.ui.proto.typed import parse_typed

STEAM = "ana_steam_k3f9"
STEAM_POWER = "ana_steam_power_x7y2"
OTHER = "bob_tools_q1w2"


class NamespaceTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mods_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def add_mod(self, mod_id, dependencies=(), nodes=None, recipes=None, goals=None, civs=None):
        folder = self.mods_dir / mod_id.replace(":", "+")
        for sub in ("branches", "production", "civilizations"):
            (folder / "data" / sub).mkdir(parents=True, exist_ok=True)
        (folder / "mod.json").write_text(json.dumps({
            "id": mod_id, "name": mod_id, "version": "1",
            "dependencies": list(dependencies), "conflicts": []}))
        if nodes is not None:
            (folder / "data/branches/n.json").write_text(json.dumps({"nodes": nodes}))
        if recipes is not None:
            (folder / "data/production/r.json").write_text(json.dumps({"materials": recipes}))
        if goals is not None:
            (folder / "data/goals.json").write_text(json.dumps({"goals": goals}))
        for name, civ in (civs or {}).items():
            (folder / "data/civilizations" / (name + ".json")).write_text(json.dumps(civ))

    def manifests(self):
        return get_ordered_mods(str(self.mods_dir))

    def tree(self):
        base = {"nodes": [{"id": "a", "name": "A", "pre": [], "lab": {}, "mat": {}}],
                "meta": {"goals": []}}
        return {node["id"]: node for node in load_mod_tree(base, self.manifests())["nodes"]}

    def reset(self):
        self.tearDown()
        self.setUp()


class ModIdFormatTests(NamespaceTestBase):
    def test_good_ids_load(self):
        for mod_id in (STEAM, STEAM_POWER, "x1_y_abcd", "ana_egypt_100bc_7k2m"):
            self.add_mod(mod_id)
        self.assertEqual(4, len(self.manifests()))

    def test_bad_ids_are_rejected_with_advice(self):
        for mod_id in ("acme", "steam_power", "ana_steam_k3", "Ana_steam_k3f9",
                       "ana_steam_K3F9", "ana_steam_k3f9:x", "_ana_steam_k3f9", "ana-steam-k3f9"):
            with self.subTest(mod_id=mod_id):
                self.reset()
                self.add_mod(mod_id)
                with self.assertRaises(ModError) as caught:
                    self.manifests()
                message = str(caught.exception)
                self.assertIn(mod_id, message)
                self.assertIn("<author>_<name>_<suffix>", message)
                self.assertIn("random", message)


class NamespaceTests(NamespaceTestBase):
    def test_namespaced_new_node_loads(self):
        self.add_mod(STEAM, nodes=[{"id": STEAM + ":engine", "name": "Engine", "pre": ["a"]}])
        self.assertIn(STEAM + ":engine", self.tree())

    def test_old_underscore_prefix_is_rejected(self):
        self.add_mod(STEAM, nodes=[{"id": STEAM + "_engine", "name": "Engine"}])
        with self.assertRaises(ModError) as caught:
            self.tree()
        self.assertIn(STEAM + ":", str(caught.exception))

    def test_prefix_mod_cannot_enter_a_longer_mods_space(self):
        self.add_mod(STEAM, nodes=[{"id": STEAM_POWER + ":engine", "name": "Engine"}])
        self.add_mod(STEAM_POWER, nodes=[{"id": STEAM_POWER + ":engine", "name": "Engine"}])
        with self.assertRaises(ModError) as caught:
            self.tree()
        self.assertIn(STEAM_POWER + ":engine", str(caught.exception))

    def test_prefix_mods_ids_never_collide(self):
        self.add_mod(STEAM, nodes=[{"id": STEAM + ":power_x7y2_engine", "name": "E"}])
        self.add_mod(STEAM_POWER, nodes=[{"id": STEAM_POWER + ":engine", "name": "E"}])
        self.assertEqual(2, len([key for key in self.tree() if ":" in key]))

    def test_recipe_ids_are_namespaced_too(self):
        recipe = {"outputs": {"m": 1}, "inputs": {}, "labour_hours": {}}
        self.add_mod(STEAM, recipes={STEAM + "_steel": recipe})
        with self.assertRaises(ModError):
            load_mod_production({}, self.manifests())
        self.reset()
        self.add_mod(STEAM, recipes={STEAM + ":steel": recipe})
        self.assertIn(STEAM + ":steel", load_mod_production({}, self.manifests()))

    def test_civilisation_ids_are_namespaced(self):
        from sim.engine.mods_civ import apply_mod_civilization
        civ = {"id": STEAM + ":land", "starting_techs": []}
        self.add_mod(STEAM, civs={STEAM + "+land": civ})
        found = apply_mod_civilization(STEAM + ":land", None, self.manifests())
        self.assertEqual(STEAM + ":land", found["id"])
        self.reset()
        self.add_mod(STEAM, civs={STEAM + "_land": {"id": STEAM + "_land", "starting_techs": []}})
        with self.assertRaises(ModError):
            apply_mod_civilization(STEAM + "_land", None, self.manifests())


class DeclaredDependencyTests(NamespaceTestBase):
    def setUp(self):
        super().setUp()
        self.add_mod(OTHER, nodes=[{"id": OTHER + ":tool", "name": "Tool"}],
                     recipes={OTHER + ":ore": {"outputs": {OTHER + ":ore": 1}, "inputs": {},
                                               "labour_hours": {}}})

    def assert_names_both(self, caught):
        message = str(caught.exception)
        self.assertIn(STEAM, message)
        self.assertIn(OTHER, message)
        self.assertIn("dependenc", message)

    def test_prerequisite_on_foreign_mod_needs_dependency(self):
        self.add_mod(STEAM, nodes=[{"id": STEAM + ":engine", "name": "E", "pre": [OTHER + ":tool"]}])
        with self.assertRaises(ModError) as caught:
            self.manifests()
        self.assert_names_both(caught)

    def test_material_reference_on_foreign_mod_needs_dependency(self):
        self.add_mod(STEAM, nodes=[{"id": STEAM + ":engine", "name": "E",
                                    "mat": {OTHER + ":ore": 1}}])
        with self.assertRaises(ModError) as caught:
            self.manifests()
        self.assert_names_both(caught)

    def test_goal_reference_needs_dependency(self):
        self.add_mod(STEAM, goals=[{"node": OTHER + ":tool"}])
        with self.assertRaises(ModError) as caught:
            self.manifests()
        self.assert_names_both(caught)

    def test_civilisation_reference_needs_dependency(self):
        self.add_mod(STEAM, civs={STEAM + "+land": {"id": STEAM + ":land",
                                                     "starting_techs": [OTHER + ":tool"]}})
        with self.assertRaises(ModError) as caught:
            self.manifests()
        self.assert_names_both(caught)

    def test_declared_dependency_loads_and_transitive_counts(self):
        self.add_mod(STEAM, dependencies=[OTHER],
                     nodes=[{"id": STEAM + ":engine", "name": "E", "pre": [OTHER + ":tool"]}])
        self.add_mod(STEAM_POWER, dependencies=[STEAM],
                     nodes=[{"id": STEAM_POWER + ":x", "name": "X", "pre": [OTHER + ":tool"]}])
        self.assertEqual(3, len(self.manifests()))

    def test_text_that_merely_mentions_a_mod_is_not_a_reference(self):
        self.add_mod(STEAM, nodes=[{"id": STEAM + ":engine", "name": "E",
                                    "note": "Borrowed from %s:tool, thanks." % OTHER}])
        self.assertEqual(2, len(self.manifests()))


class PlayerFacingTests(unittest.TestCase):
    def test_typed_command_keeps_namespaced_id_whole(self):
        for text in ("start %s:engine" % STEAM, "why %s:engine" % STEAM):
            command, error = parse_typed(text)
            self.assertIsNone(error, error)
            self.assertEqual(STEAM + ":engine", command["id"])

    def test_key_colon_flags_still_work(self):
        command, error = parse_typed("available all:true")
        self.assertIsNone(error)
        self.assertTrue(command.get("all"))

    def test_fog_scrubs_a_namespaced_id_whole(self):
        from sim.tests.harness import sim
        game = sim(capital=1000.0)
        game.fog = True
        hidden, visible = STEAM + ":engine", STEAM + ":gear"
        text = "needs %s and %s, then %s." % (hidden, visible, hidden)
        # patch.dict restores the shared node table afterwards
        with mock.patch.dict(game.nodes, {hidden: {"name": "x"}, visible: {"name": "x"}}), \
                mock.patch.object(game, "is_visible",
                                  side_effect=lambda node_id, **_: node_id == visible):
            scrubbed = game.fog_scrub(text)
        self.assertNotIn("engine", scrubbed)
        self.assertIn(visible, scrubbed)
        self.assertEqual(2, scrubbed.count("something you have not heard of"))

    def test_fog_does_not_cut_a_visible_id_at_the_colon(self):
        from sim.tests.harness import sim
        game = sim(capital=1000.0)
        game.fog = True
        visible = STEAM + ":wheel"
        with mock.patch.dict(game.nodes, {visible: {"name": "x"}, "wheel": {"name": "y"}}), \
                mock.patch.object(game, "is_visible",
                                  side_effect=lambda node_id, **_: node_id == visible):
            scrubbed = game.fog_scrub("the %s and the wheel" % visible)
        self.assertIn(visible, scrubbed)
        self.assertEqual(1, scrubbed.count("something you have not heard of"))


class BundledModsTests(unittest.TestCase):
    def test_sample_mods_follow_the_format(self):
        from sim.engine.mods_ids import MOD_ID_PATTERN
        repo = Path(__file__).resolve().parents[2]
        manifests = get_ordered_mods(str(repo / "mods"))
        self.assertTrue(manifests)
        for manifest in manifests:
            self.assertRegex(manifest.id, MOD_ID_PATTERN)


if __name__ == "__main__":
    unittest.main()
