"""A mod's code is handed the views and commands it declared and nothing else: the access refuses an undeclared view or command
naming the mod and the name, guards what a view answers, keeps the mod's own saved memory, and the assembly refuses a declaration
of a view no module publishes. Each provider a mod gives to an extension point receives its mod's access. Toy assemblies, no game."""
QUICK_TOPIC = True

import unittest

from sim.assembly.api import (LIST, AssemblyError, ExtensionPoint, Module, ModuleSpec, Operations, UndeclaredRead, UndeclaredSend,
                              ViewSpec, ViewWrite, assemble)
from sim.engine.mod_code import ModCodeApi
from sim.tests.assembly_fixture import BASE, TOP, SetValue, Unapplied, build

MOD = "test_acme_s7q2"
OTHER = "test_beta_s7q2"


class Table(Module):
    def table(self):
        return {"rows": [1, 2]}


TABLE = ModuleSpec("table", Table, publishes=(ViewSpec("table", "table", cached=False),))


def with_reads(*views, sends=()):
    return build(TABLE, operations=[Operations(MOD, reads=tuple(views), sends=tuple(sends))])


class DeclaredReads(unittest.TestCase):
    def test_a_declared_view_answers_as_the_game_does(self):
        assembly = with_reads("double", "table")
        access = assembly.mod_access[MOD]
        self.assertEqual(access.view("double")(), 2)
        self.assertEqual(access.view("table")()["rows"], [1, 2])

    def test_an_undeclared_view_is_refused_naming_the_mod_and_the_view(self):
        access = with_reads("double").mod_access[MOD]
        with self.assertRaises(UndeclaredRead) as caught:
            access.view("raw")
        self.assertEqual((caught.exception.mod_id, caught.exception.view), (MOD, "raw"))

    def test_another_mods_declaration_does_not_open_a_view(self):
        assembly = build(TABLE, operations=[Operations(MOD, reads=("double",)), Operations(OTHER, reads=("raw",))])
        self.assertEqual(assembly.mod_access[OTHER].view("raw")(), 1)
        with self.assertRaises(UndeclaredRead):
            assembly.mod_access[OTHER].view("double")

    def test_an_answer_cannot_be_written_through(self):
        answer = with_reads("table").mod_access[MOD].view("table")()
        with self.assertRaises(ViewWrite):
            answer["rows"].append(3)

    def test_a_mod_that_declared_nothing_reads_nothing(self):
        access = build(TABLE, operations=[Operations(MOD)]).mod_access[MOD]
        with self.assertRaises(UndeclaredRead):
            access.view("double")


class DeclaredSends(unittest.TestCase):
    def test_a_declared_command_is_applied_by_its_owner(self):
        assembly = with_reads("raw", sends=(SetValue,))
        assembly.mod_access[MOD].send(SetValue(9))
        self.assertEqual(assembly.views["raw"](), 9)

    def test_an_undeclared_command_is_refused_naming_the_mod_and_the_command(self):
        access = with_reads("raw", sends=(SetValue,)).mod_access[MOD]
        with self.assertRaises(UndeclaredSend) as caught:
            access.send(Unapplied())
        self.assertEqual((caught.exception.mod_id, caught.exception.command), (MOD, "Unapplied"))


class Memory(unittest.TestCase):
    def test_the_mods_memory_is_its_own_dict_inside_the_saved_game(self):
        saved = {}
        assembly = with_reads("raw")
        assembly.mod_memory = lambda: saved
        assembly.mod_access[MOD].memory()["count"] = 3
        self.assertEqual(saved, {"mod_state": {MOD: {"count": 3}}})


class AssemblyChecks(unittest.TestCase):
    def test_a_read_of_a_view_no_module_publishes_is_refused_naming_the_mod_and_the_view(self):
        with self.assertRaises(AssemblyError) as caught:
            with_reads("no_such_view")
        self.assertIn(MOD, str(caught.exception))   # presentation: the refusal names the mod and the view
        self.assertIn("no_such_view", str(caught.exception))

    def test_a_send_no_module_applies_is_refused_naming_the_mod(self):
        with self.assertRaises(AssemblyError) as caught:
            with_reads("raw", sends=(Unapplied,))
        self.assertIn(MOD, str(caught.exception))   # presentation: the refusal names the mod and the command
        self.assertIn("Unapplied", str(caught.exception))

    def test_removing_a_module_a_mod_reads_is_refused_naming_both(self):
        with self.assertRaises(AssemblyError) as caught:
            build(operations=[Operations(MOD, reads=("double",)), Operations(OTHER, removed=("base",))])
        for party in (MOD, OTHER, "double"):
            self.assertIn(party, str(caught.exception))   # presentation: names the reader, the remover and the view


class Owner(Module):
    pass


POINTS = ModuleSpec("owner", Owner, extension_points=tuple(ExtensionPoint(name, LIST) for name in (
    "externality", "town_population", "town_mortality_premium", "director_overhead", "wealth_claims")))


def provided_game(register):
    api = ModCodeApi(MOD)
    register(api)
    return assemble([BASE, TOP, POINTS], [api.operations])


class Providers(unittest.TestCase):
    def test_the_externality_provider_receives_its_mods_access_and_the_year(self):
        received = []
        game = provided_game(lambda api: (api.reads("double"), api.externality(lambda access, year: received.append((access, year)))))
        game.points["externality"](1300)
        self.assertEqual(received, [(game.mod_access[MOD], 1300)])

    def test_the_town_providers_receive_their_mods_access_the_tile_and_the_size(self):
        received = []
        game = provided_game(lambda api: (api.reads("double"), api.town_provider(
            "towns", lambda access, tile, nominal: received.append(("size", access, tile, nominal)),
            mortality_premium=lambda access, tile, town: received.append(("premium", access, tile, town)))))
        game.points["town_population"]("t1", 100.0)
        game.points["town_mortality_premium"]("t1", 80.0)
        access = game.mod_access[MOD]
        self.assertEqual(received, [("size", access, "t1", 100.0), ("premium", access, "t1", 80.0)])

    def test_the_director_overhead_provider_receives_its_mods_access(self):
        game = provided_game(lambda api: (api.reads("double"), api.director_overhead(lambda access: access.view("double")() * 10.0)))
        self.assertEqual(game.points["director_overhead"](), [20.0])

    def test_the_wealth_claim_reader_and_seizer_receive_their_mods_access(self):
        received = []
        game = provided_game(lambda api: (api.reads("raw"), api.wealth_claims(
            lambda access: received.append(("owed", access)) or access.view("raw")() * 5.0,
            lambda access, amount, taker: received.append(("seized", access, amount, taker)) or 1.0)))
        (owed, seize), = game.points["wealth_claims"]()
        self.assertEqual(owed(), 5.0)
        self.assertEqual(seize(7.0, "treasury"), 1.0)
        access = game.mod_access[MOD]
        self.assertEqual(received, [("owed", access), ("seized", access, 7.0, "treasury")])

    def test_a_provider_cannot_read_what_its_mod_did_not_declare(self):
        game = provided_game(lambda api: api.director_overhead(lambda access: access.view("double")()))
        with self.assertRaises(UndeclaredRead) as caught:
            game.points["director_overhead"]()
        self.assertEqual((caught.exception.mod_id, caught.exception.view), (MOD, "double"))


if __name__ == "__main__":
    unittest.main()
