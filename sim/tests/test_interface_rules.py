"""The interface module's rule, one function: `declare` turns every provider's declarations into a game's commands and figures.
A word or a figure name answered twice is an error naming both owners; patches change or remove a command that exists; a macro
or policy names only commands that exist, and a macro never names a macro."""
QUICK_TOPIC = True

import unittest

from sim.interface.api import (CODE, MACRO, PATCH, POLICY, READ, SHIPPED, SHIPPED_OWNER, CommandDeclaration, FigureDeclaration,
                               declare, entry_fields)
from sim.mod_errors import ModError

ACME, BETA = "test_acme_k3f9", "test_beta_k3f9"


def fields(summary="s", aliases=()):
    return dict(group="game", summary=summary, usage=["u"], description="d", options=None, aliases=list(aliases), shape="bare")


def shipped(name, aliases=()):
    return CommandDeclaration(SHIPPED_OWNER, name, SHIPPED, fields(aliases=aliases), lambda sim, nodes, cmd, ended: {})


def coded(owner, name, aliases=()):
    return CommandDeclaration(owner, name, CODE, fields(aliases=aliases), lambda sim, nodes, cmd, ended: {})


def macro(owner, name, steps):
    spec = {"kind": "macro", "summary": "s", "description": "d", "steps": [{"cmd": step} for step in steps]}
    return CommandDeclaration(owner, name, MACRO, entry_fields(spec, name), None, spec)


def figure(owner, name):
    return FigureDeclaration(owner, name, name, "", 1, lambda sim: {"value": 1.0})


class CommandTests(unittest.TestCase):
    def test_commands_are_kept_in_provider_order_with_who_owns_each_word(self):
        declared = declare([[shipped("state", aliases=("s",))], [coded(ACME, ACME + ":hello")]], [])
        self.assertEqual(list(declared.commands), ["state", ACME + ":hello"])
        self.assertEqual(declared.owners, {"state": SHIPPED_OWNER, "s": SHIPPED_OWNER, ACME + ":hello": ACME})
        self.assertEqual(declared.kinds, {ACME + ":hello": CODE})

    def test_a_word_two_mods_claim_is_an_error_naming_both(self):
        with self.assertRaises(ModError) as caught:
            declare([[coded(ACME, ACME + ":a", aliases=("hi",))], [coded(BETA, BETA + ":b", aliases=("hi",))]], [])
        self.assertIn(ACME, str(caught.exception))   # presentation: the error text names both owners
        self.assertIn(BETA, str(caught.exception))

    def test_an_alias_may_not_shadow_a_shipped_command(self):
        with self.assertRaises(ModError) as caught:
            declare([[shipped("state")], [coded(ACME, ACME + ":a", aliases=("state",))]], [])
        self.assertIn("the shipped game", str(caught.exception))   # presentation: names the holder

    def test_a_patch_replaces_the_help_of_a_command_that_exists_and_leaves_the_declaration_alone(self):
        original = shipped("quit")
        patch = CommandDeclaration(ACME, "quit", PATCH, spec={"override": True, "summary": "leave now"})
        declared = declare([[original], [patch]], [])
        self.assertEqual(declared.commands["quit"]["summary"], "leave now")
        self.assertEqual(original.fields["summary"], "s")

    def test_a_remove_patch_drops_the_command_and_its_words(self):
        patch = CommandDeclaration(ACME, "score", PATCH, spec={"remove": True})
        declared = declare([[shipped("score", aliases=("points",)), shipped("state")], [patch]], [])
        self.assertEqual(list(declared.commands), ["state"])
        self.assertNotIn("points", declared.owners)

    def test_a_patch_of_a_missing_command_is_an_error_naming_the_mod(self):
        with self.assertRaises(ModError) as caught:
            declare([[shipped("state")], [CommandDeclaration(ACME, "nonsense", PATCH, spec={"remove": True})]], [])
        self.assertIn(ACME, str(caught.exception))   # presentation: names the mod

    def test_a_macro_naming_a_command_removed_by_a_patch_is_an_error(self):
        patch = CommandDeclaration(ACME, "score", PATCH, spec={"remove": True})
        with self.assertRaises(ModError):
            declare([[shipped("score")], [macro(ACME, ACME + ":m", ["score"])], [patch]], [])

    def test_a_macro_may_not_name_a_macro(self):
        with self.assertRaises(ModError):
            declare([[shipped("state")], [macro(ACME, ACME + ":a", ["state"]), macro(ACME, ACME + ":b", [ACME + ":a"])]], [])

    def test_a_policy_names_commands_that_exist(self):
        spec = {"kind": "policy", "hook": "year_start", "summary": "s", "description": "d", "do": [{"cmd": "nonsense"}]}
        with self.assertRaises(ModError):
            declare([[shipped("state")], [CommandDeclaration(ACME, ACME + ":p", POLICY, spec=spec)]], [])

    def test_a_policy_is_kept_beside_the_commands_not_among_them(self):
        spec = {"kind": "policy", "hook": "year_start", "summary": "s", "description": "d", "do": [{"cmd": "state"}]}
        declared = declare([[shipped("state")], [CommandDeclaration(ACME, ACME + ":p", POLICY, spec=spec)]], [])
        self.assertEqual(declared.policies, [(ACME + ":p", spec)])
        self.assertNotIn(ACME + ":p", declared.commands)

    def test_a_read_command_declared_as_data_takes_its_fields_from_the_spec(self):
        spec = {"kind": "read", "summary": "people", "description": "d", "aliases": ["headcount"], "shows": []}
        declaration = CommandDeclaration(ACME, ACME + ":census", READ, entry_fields(spec, ACME + ":census"), None, spec)
        declared = declare([[declaration]], [])
        self.assertEqual(declared.commands[ACME + ":census"]["aliases"], ["headcount"])
        self.assertEqual(declared.commands[ACME + ":census"]["group"], "mods")


class FigureTests(unittest.TestCase):
    def test_figures_are_kept_in_provider_order_with_their_owner(self):
        declared = declare([], [[figure(SHIPPED_OWNER, "cash")], [figure(ACME, ACME + ":mana")]])
        self.assertEqual(list(declared.figures), ["cash", ACME + ":mana"])
        self.assertEqual(declared.figure_owners, {"cash": SHIPPED_OWNER, ACME + ":mana": ACME})

    def test_a_figure_two_providers_declare_is_an_error_naming_both(self):
        with self.assertRaises(ModError) as caught:
            declare([], [[figure(ACME, "mana")], [figure(BETA, "mana")]])
        self.assertIn(ACME, str(caught.exception))   # presentation: the error text names both owners
        self.assertIn(BETA, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
