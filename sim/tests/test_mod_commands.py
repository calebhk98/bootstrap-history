"""Mods add, change and remove player commands and automatic policies, as data and as consented code."""

QUICK_TOPIC = True

import json
import unittest.mock
from types import SimpleNamespace
import unittest

from sim.engine import mod_code
from sim.engine.mods import ModError
from sim.engine.ui_commands import policy_defaults
from sim.tests.test_mod_removal_and_civs import ModTestBase
from sim.ui.proto import command_registry, mod_commands
from sim.ui.proto.dispatch import _agent_dispatch_inner

ACME = "test_acme_k3f9"
BETA = "test_beta_k3f9"


def fake_sim():
    return SimpleNamespace(
        nodes={}, fog=False, cfg={"start_year": 0, "horizon_years": 10}, dead_reason=None, year=1, end_year=10,
        population=SimpleNamespace(total=1234.567), policy={ACME + ":pulse": True}, ran=[])


class CommandTestBase(ModTestBase):
    def setUp(self):
        super().setUp()
        mod_commands.forget_mod_commands()
        mod_code.LOADED.clear()
        mod_code.COMMAND_REGISTRATIONS.clear()

    def tearDown(self):
        mod_commands.forget_mod_commands()
        mod_code.LOADED.clear()
        mod_code.COMMAND_REGISTRATIONS.clear()
        super().tearDown()

    def write_commands(self, mod_id, commands):
        path = self.mods_dir / mod_id / "data" / "ui" / "commands.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"commands": commands}))

    def load(self):
        mod_commands.load_mod_commands(str(self.mods_dir))

    def run_command(self, name, **fields):
        return _agent_dispatch_inner(fake_sim(), {}, dict(fields, cmd=name))


READ = {"kind": "read", "summary": "people", "description": "Shows the population.", "aliases": ["headcount"],
        "shows": [{"label": "People", "path": "population.total", "unit": "people", "digits": 1}]}


class DataCommandTests(CommandTestBase):
    def test_read_command_is_registered_and_answers(self):
        self.add_mod(ACME)
        self.write_commands(ACME, {ACME + ":census": READ})
        self.load()
        reply = self.run_command(ACME + ":census")
        self.assertEqual(reply["values"], [{"label": "People", "value": 1234.6, "unit": "people"}])
        self.assertIn("headcount", command_registry.alias_map())
        self.assertEqual(command_registry.resolve("headcount")["name"], ACME + ":census")

    def test_help_page_comes_from_the_registry(self):
        self.add_mod(ACME)
        self.write_commands(ACME, {ACME + ":census": READ})
        self.load()
        self.assertEqual(command_registry.page(ACME + ":census")["summary"], "people")

    def test_private_state_path_is_refused_at_load(self):
        self.add_mod(ACME)
        bad = dict(READ, shows=[{"label": "x", "path": "population._hidden"}])
        self.write_commands(ACME, {ACME + ":census": bad})
        with self.assertRaises(ModError):
            self.load()

    def test_command_outside_the_namespace_is_refused(self):
        self.add_mod(ACME)
        self.write_commands(ACME, {"census": READ})
        with self.assertRaises(ModError):
            self.load()

    def test_alias_clash_between_mods_names_both(self):
        self.add_mod(ACME)
        self.add_mod(BETA)
        self.write_commands(ACME, {ACME + ":census": READ})
        self.write_commands(BETA, {BETA + ":census": READ})
        with self.assertRaises(ValueError) as caught:
            self.load()
        self.assertIn(ACME, str(caught.exception))
        self.assertIn(BETA, str(caught.exception))

    def test_alias_may_not_shadow_a_shipped_command(self):
        self.add_mod(ACME)
        self.write_commands(ACME, {ACME + ":census": dict(READ, aliases=["state"])})
        with self.assertRaises(ValueError):
            self.load()

    def test_macro_replays_commands_and_substitutes_fields(self):
        self.add_mod(ACME)
        seen = []
        command_registry.register_command(
            "zz_echo", group="game", summary="s", usage=["zz_echo"], description="d",
            handler=lambda sim, nodes, cmd, ended: seen.append(cmd) or {"ok": True})
        self.addCleanup(command_registry.unregister, "zz_echo")
        self.write_commands(ACME, {ACME + ":twice": {
            "kind": "macro", "summary": "s", "description": "d", "shape": "text",
            "steps": [{"cmd": "zz_echo", "text": "$text"}, {"cmd": "zz_echo", "text": "again"}]}})
        self.load()
        reply = self.run_command(ACME + ":twice", text="hello")
        self.assertTrue(reply["ok"])
        self.assertEqual([item["text"] for item in seen], ["hello", "again"])

    def test_macro_missing_field_runs_nothing(self):
        self.add_mod(ACME)
        self.write_commands(ACME, {ACME + ":m": {
            "kind": "macro", "summary": "s", "description": "d", "steps": [{"cmd": "quit", "text": "$text"}]}})
        self.load()
        reply = self.run_command(ACME + ":m")
        self.assertFalse(reply["ok"])
        self.assertIn("text", reply["error"])

    def test_macro_naming_a_missing_command_fails_at_load(self):
        self.add_mod(ACME)
        self.write_commands(ACME, {ACME + ":m": {
            "kind": "macro", "summary": "s", "description": "d", "steps": [{"cmd": "no_such_command"}]}})
        with self.assertRaises(ValueError) as caught:
            self.load()
        self.assertIn("no_such_command", str(caught.exception))

    def test_macro_may_not_name_a_macro(self):
        self.add_mod(ACME)
        first = {"kind": "macro", "summary": "s", "description": "d", "steps": [{"cmd": "state"}]}
        second = {"kind": "macro", "summary": "s", "description": "d", "steps": [{"cmd": ACME + ":a"}]}
        self.write_commands(ACME, {ACME + ":a": first, ACME + ":b": second})
        with self.assertRaises(ValueError) as caught:
            self.load()
        self.assertIn("macro", str(caught.exception))

    def test_override_changes_help_and_remove_deletes_then_restores(self):
        self.add_mod(ACME)
        self.write_commands(ACME, {"quit": {"override": True, "summary": "leave the game now"},
                                   "score": {"remove": True}})
        self.load()
        self.assertEqual(command_registry.COMMANDS["quit"]["summary"], "leave the game now")
        self.assertNotIn("score", command_registry.COMMANDS)
        mod_commands.forget_mod_commands()
        self.assertIn("score", command_registry.COMMANDS)
        self.assertNotEqual(command_registry.COMMANDS["quit"]["summary"], "leave the game now")

    def test_removing_a_command_a_macro_uses_fails_at_load(self):
        self.add_mod(ACME)
        self.write_commands(ACME, {"score": {"remove": True}, ACME + ":m": {
            "kind": "macro", "summary": "s", "description": "d", "steps": [{"cmd": "score"}]}})
        try:
            with self.assertRaises(ValueError):
                self.load()
        finally:
            mod_commands.forget_mod_commands()

    def test_changing_a_missing_command_is_an_error(self):
        self.add_mod(ACME)
        self.write_commands(ACME, {"nonsense": {"remove": True}})
        with self.assertRaises(ValueError):
            self.load()


class PolicyTests(CommandTestBase):
    POLICY = {"kind": "policy", "summary": "s", "description": "d", "hook": "year_start",
              "when": [{"path": "population.total", "op": ">=", "value": 1000}],
              "do": [{"cmd": "zz_mark"}]}

    def setUp(self):
        super().setUp()
        self.marks = []
        command_registry.register_command(
            "zz_mark", group="game", summary="s", usage=["zz_mark"], description="d",
            handler=lambda sim, nodes, cmd, ended: self.marks.append(sim.year) or {"ok": True})
        self.addCleanup(command_registry.unregister, "zz_mark")

    def test_policy_runs_when_on_and_condition_holds(self):
        self.add_mod(ACME)
        self.write_commands(ACME, {ACME + ":pulse": self.POLICY})
        self.load()
        sim = fake_sim()
        lines = mod_commands.run_policies(sim, {}, "year_start")
        self.assertEqual(self.marks, [1])
        self.assertIn(ACME + ":pulse", lines[0])
        self.assertEqual(mod_commands.run_policies(sim, {}, "year_end"), [])

    def test_policy_off_or_condition_false_does_nothing(self):
        self.add_mod(ACME)
        self.write_commands(ACME, {ACME + ":pulse": self.POLICY})
        self.load()
        sim = fake_sim()
        sim.policy[ACME + ":pulse"] = False
        mod_commands.run_policies(sim, {}, "year_start")
        sim.policy[ACME + ":pulse"] = True
        sim.population.total = 5
        mod_commands.run_policies(sim, {}, "year_start")
        self.assertEqual(self.marks, [])

    def test_policy_is_a_switch_in_a_new_seats_policy(self):
        self.add_mod(ACME)
        self.write_commands(ACME, {ACME + ":pulse": dict(self.POLICY, default=False)})
        self.assertIs(policy_defaults(False, mods_dir=str(self.mods_dir))[ACME + ":pulse"], False)

    def test_mod_sets_the_default_of_a_shipped_switch(self):
        self.add_mod(ACME)
        path = self.mods_dir / ACME / "data" / "ui" / "policies.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"defaults": {"auto_mine": False}}))
        self.assertIs(policy_defaults(False, mods_dir=str(self.mods_dir))["auto_mine"], False)

    def test_unrelated_mods_setting_one_switch_name_both(self):
        for mod_id in (ACME, BETA):
            self.add_mod(mod_id)
            path = self.mods_dir / mod_id / "data" / "ui" / "policies.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"defaults": {"auto_mine": mod_id == ACME}}))
        with self.assertRaises(ModError) as caught:
            policy_defaults(False, mods_dir=str(self.mods_dir))
        self.assertIn(ACME, str(caught.exception))
        self.assertIn(BETA, str(caught.exception))


CODE = '''
import os
MARKER = os.environ.get("MOD_CODE_MARKER")
if MARKER:
    open(MARKER, "w").write("ran")

def register(api):
    @api.command("hello", group="game", summary="s", usage=["hello"], description="d")
    def hello(sim, nodes, cmd, ended):
        return {"ok": True, "greeting": "hi", "mod": api.mod_id}
'''


class CodeTests(CommandTestBase):
    def add_code_mod(self, source=CODE, permissions=("code",)):
        self.add_mod(ACME)
        folder = self.mods_dir / ACME
        (folder / "hello.py").write_text(source)
        manifest = json.loads((folder / "mod.json").read_text())
        manifest.update(code=["hello.py"], permissions=list(permissions))
        (folder / "mod.json").write_text(json.dumps(manifest))

    def test_unallowed_code_does_not_run(self):
        self.add_code_mod()
        marker = self.root / "marker"
        with unittest.mock.patch.dict("os.environ", {"MOD_CODE_MARKER": str(marker)}):
            self.load()
        self.assertFalse(marker.exists())
        self.assertNotIn(ACME + ":hello", command_registry.COMMANDS)
        self.assertEqual(mod_code.LOADED[ACME], "no consent")
        self.assertIn("NOT allowed", mod_code.code_report(str(self.mods_dir))[0])

    def test_allowed_code_registers_a_namespaced_command(self):
        self.add_code_mod()
        mod_code.allow(str(self.mods_dir), ACME)
        self.load()
        self.assertEqual(self.run_command(ACME + ":hello")["greeting"], "hi")
        self.assertNotIn("hello", command_registry.COMMANDS)

    def test_a_changed_file_needs_consent_again(self):
        self.add_code_mod()
        mod_code.allow(str(self.mods_dir), ACME)
        (self.mods_dir / ACME / "hello.py").write_text(CODE + "\n# edited\n")
        self.load()
        self.assertNotIn(ACME + ":hello", command_registry.COMMANDS)

    def test_code_without_permission_declaration_is_refused(self):
        self.add_code_mod(permissions=())
        with self.assertRaises(ModError):
            self.load()

    def test_code_file_outside_the_mod_is_refused(self):
        self.add_code_mod()
        path = self.mods_dir / ACME / "mod.json"
        manifest = json.loads(path.read_text())
        manifest["code"] = ["../escape.py"]
        path.write_text(json.dumps(manifest))
        (self.mods_dir / "escape.py").write_text(CODE)
        mod_code.COMMAND_REGISTRATIONS.clear()
        with self.assertRaises(ModError):
            mod_code.allow(str(self.mods_dir), ACME)

    def test_command_state_lives_in_the_saved_memory(self):
        api = mod_code.ModCodeApi(ACME)
        memory = {}
        api.state(memory)["count"] = 3
        self.assertEqual(memory, {"mod_state": {ACME: {"count": 3}}})


if __name__ == "__main__":
    unittest.main()
