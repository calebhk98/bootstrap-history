"""SMOKE: each operation a mod's code can ask of the assembly, in a whole game. Every case writes a small consented code mod into
a temporary mods directory and builds three games in one process: before it, over it, and after it. Replace a module (the game
answers through the replacement), remove one (refused while a module still reads it, naming the readers and the remover;
accepted when nothing does), add one (its state is saved and loaded, its view and command are reachable), extend one (a layer
overrides a method and `super()` reaches the shipped one), adjust a view (stacked adjusters apply in mod load order), provide
to an extension point and withdraw a shipped provision. The games before and after the mod never see it. The rules are tested one
function at a time in test_assembly_mod_operations and test_interface_rules."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Optional, Tuple
from unittest import mock

from sim.assembly.api import AssemblyError, UndeclaredRead
from sim.engine import bridge_land, mod_code
from sim.engine.saveload import load_state, save_state
from sim.mod_errors import ModError
from sim.stores.api import WriteStore
from sim.tests.harness import unopened_sim
from sim.ui.figures import FIGURES, figures_of, read_figure
from sim.ui.proto import command_registry
from sim.ui.proto.dispatch import _agent_dispatch_inner

SWAP, STRIP, STRIP_ONE, TEMPLE, LAYER, ALPHA, BETA, GIVER, TAKER = (
    "test_swap_s7q2", "test_strip_s7q2", "test_stripone_s7q2", "test_temple_s7q2", "test_layer_s7q2", "test_alpha_s7q2",
    "test_beta_s7q2", "test_giver_s7q2", "test_taker_s7q2")
BASE_STORE = "control"   # a store the base game declares, so every game has it

REPLACE = '''
import dataclasses
from sim.stores.module import Stores
from sim.stores.module_spec import MODULE_SPECS


class SwappedStores(Stores):
    def setup(self):
        super().setup()
        self.writes = []

    def store(self, name):
        return dict(super().store(name), served_by=MOD)

    def write_store(self, command):
        self.writes.append((command.store, command.key))
        return super().write_store(command)


def register(api):
    api.replace_module("stores", dataclasses.replace(MODULE_SPECS[0], implementation=SwappedStores))
'''

REMOVE = '''
def register(api):
    api.remove_module(%r)
'''

ADD = '''
import dataclasses
from sim.assembly.api import Command, Module, ModuleSpec, ViewSpec


@dataclasses.dataclass
class Tally:
    visits: int = 0
    names: list = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class Visit(Command):
    name: str


class Temple(Module):
    def visits(self):
        return {"visits": self.world.visits, "names": list(self.world.names)}

    def apply_visit(self, command):
        self.world.visits += 1
        self.world.names.append(command.name)
        self.bump("visits")
        return self.world.visits


def register(api):
    api.add_module(ModuleSpec(api.qualified("temple"), Temple, channels=("visits",), world_state=Tally,
                              publishes=(ViewSpec(api.qualified("visits"), "visits", channels=("visits",)),),
                              applies=((Visit, "apply_visit"),)))

    api.sends(Visit)

    @api.command("visit", group="game", summary="a visit", usage=["visit"], description="Visit the temple.")
    def visit(access, nodes, cmd, ended):
        return {"ok": True, "visits": access.send(Visit(cmd.get("text", "pilgrim")))}
'''

EXTEND = '''
class Layered:
    def store(self, name):
        answer = super().store(name)
        return dict(answer, layered_by=MOD, shipped_keys=sorted(answer))

    def helper(self):
        return 1   # not part of the module's declared methods: `validate` labels the layer unstable


def register(api):
    api.extend_module("stores", Layered)
'''

ADJUST = '''
def register(api):
    api.adjust_view("store", lambda access, value, key: dict(value, adjusted_by=list(value.get("adjusted_by", [])) + [MOD, key]),
                    reads=("acting_seat",))
'''

PROVIDE = '''
def register(api):
    api.provide("actor_spawners", lambda: [(MOD + ":founding", lambda registry, world: [])])
    api.provide("director_overhead", lambda: 50.0)
'''

WITHDRAW = '''
def register(api):
    api.withdraw("actors.spawners")
    api.spawner("only", lambda registry, world: [])
'''


FIGURE = '''
def register(api):
    @api.figure("mana", "Mana", unit="mana")
    def mana(sim):
        return {"value": 7.0, "components": {"temples": 7.0}}
'''

EFFECTS = '''
def register(api):
    api.uses_effects("record_event")

    @api.command("omen", group="game", summary="an omen", usage=["omen"], description="Record an omen.")
    def omen(access, nodes, cmd, ended):
        return {"ok": True, "kind": api.effects.record_event(access, "omen", "a comet")["kind"]}

    @api.command("curse", group="game", summary="a curse", usage=["curse"], description="Pay without declaring it.")
    def curse(access, nodes, cmd, ended):
        api.effects.pay(access, "government:x", "government:y", 1.0, "a gift")
        return {"ok": True}
'''

SAME_WORD = '''
def register(api):
    api.command("greet", group="game", summary="s", usage=["greet"], description="d", aliases=["hi"])(lambda sim, nodes, cmd, ended: {"ok": True})
'''


def write_mod(mods_dir: Path, mod_id: str, source: str, dependencies: Tuple[str, ...] = ()) -> None:
    folder = mods_dir / mod_id
    (folder / "data").mkdir(parents=True)
    (folder / "mod.json").write_text(json.dumps({"id": mod_id, "name": mod_id, "version": "1", "dependencies": list(dependencies),
                                                 "conflicts": [], "code": ["hooks.py"], "permissions": ["code"]}))
    (folder / "hooks.py").write_text('MOD = %r\n' % mod_id + source)


class OperationCase(unittest.TestCase):
    """Games before, over and after the mods of `MODS` (mod id -> (source, dependencies)); `game_over` builds more."""
    MODS: Dict[str, Tuple[str, Tuple[str, ...]]] = {}
    modded = None
    refused: Optional[AssemblyError] = None

    @classmethod
    def game_over(cls, mods: Dict[str, Tuple[str, Tuple[str, ...]]]):
        mods_dir = Path(cls.tmp.name) / ("mods_%d" % len(cls.directories))
        cls.directories.append(mods_dir)
        for mod_id, (source, dependencies) in mods.items():
            write_mod(mods_dir, mod_id, source, dependencies)
        for mod_id in mods:
            mod_code.allow(str(mods_dir), mod_id)   # once every mod is in place, so a dependency exists when its dependant is read
        with mock.patch.object(bridge_land, "MODS_DIR", str(mods_dir)):
            return unopened_sim()

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.directories = []
        cls.before = unopened_sim()
        try:
            cls.modded = cls.game_over(cls.MODS)
        except AssemblyError as error:
            cls.refused = error
        cls.prepare()
        cls.after = unopened_sim()

    @classmethod
    def prepare(cls):
        """Built over the mods, before the game after them: a case's own extra games."""

    @classmethod
    def tearDownClass(cls):
        mod_code.LOADED.clear()
        mod_code.MOD_OPERATIONS.clear()
        cls.tmp.cleanup()

    def plain_games(self):
        return (self.before, self.after)


class ReplaceModuleTests(OperationCase):
    MODS = {SWAP: (REPLACE, ())}

    def test_the_assembly_records_the_replacement_in_its_game_only(self):
        self.assertEqual(self.modded.assembly.applied.replaced_by, {"stores": SWAP})
        for plain in self.plain_games():
            self.assertEqual(plain.assembly.applied.replaced_by, {})

    def test_the_game_answers_a_view_through_the_replacement(self):
        self.assertEqual(self.modded.view("store")[BASE_STORE]["served_by"], SWAP)
        for plain in self.plain_games():
            self.assertNotIn("served_by", plain.view("store")[BASE_STORE])

    def test_the_replacement_publishes_the_same_answer_the_shipped_module_did(self):
        answer = dict(self.modded.view("store")[BASE_STORE])
        del answer["served_by"]
        self.assertEqual(answer, self.before.view("store")[BASE_STORE])

    def test_the_game_applies_a_command_through_the_replacement(self):
        game = self.game_over(self.MODS)
        game.send(WriteStore(BASE_STORE, "tile_1", 3))
        self.assertEqual(game.assembly.modules["stores"].writes, [(BASE_STORE, "tile_1")])
        self.assertEqual(game.view("store")[BASE_STORE]["values"], {"tile_1": 3})
        for plain in self.plain_games():
            self.assertEqual(plain.view("store")[BASE_STORE]["values"], {})


class ReplaceRefusedTests(OperationCase):
    THIN = '''
import dataclasses
from sim.stores.module import Stores
from sim.stores.module_spec import MODULE_SPECS


def register(api):
    api.replace_module("stores", dataclasses.replace(MODULE_SPECS[0], implementation=Stores, publishes=MODULE_SPECS[0].publishes[:1]))
'''
    MODS = {SWAP: (THIN, ())}

    def test_a_replacement_that_leaves_out_a_view_is_refused_naming_the_mod_and_the_view(self):
        self.assertIsNotNone(self.refused)
        self.assertIn(SWAP, str(self.refused))   # presentation: the error text names the mod and what is missing
        self.assertIn("store", str(self.refused))

    def test_the_games_before_and_after_keep_the_shipped_module(self):
        for plain in self.plain_games():
            self.assertEqual(plain.assembly.applied.replaced_by, {})


class RemoveRefusedTests(OperationCase):
    MODS = {STRIP: (REMOVE % "stores", ())}

    def test_the_game_is_refused_at_assembly(self):
        self.assertIsNotNone(self.refused)
        self.assertIsNone(self.modded)

    def test_the_refusal_names_the_remover_and_every_reader(self):
        for party in (STRIP, "stores", "campaigns", "land"):
            self.assertIn(party, str(self.refused))   # presentation: the error text names the remover, the module and each reader

    def test_games_before_and_after_still_have_the_module(self):
        for plain in self.plain_games():
            self.assertIn("stores", plain.assembly.modules)


class RemoveAcceptedTests(OperationCase):
    MODS = {STRIP_ONE: (REMOVE % "campaigns", ())}

    def test_the_game_has_no_such_module_and_no_state_for_it(self):
        self.assertIsNone(self.refused)
        self.assertNotIn("campaigns", self.modded.assembly.modules)
        self.assertNotIn("campaigns", self.modded.state.modules)
        self.assertEqual(self.modded.assembly.applied.removed_by, {"campaigns": STRIP_ONE})

    def test_its_views_are_gone_from_its_game_only(self):
        with self.assertRaises(KeyError):
            self.modded.view("armies")
        for plain in self.plain_games():
            self.assertIn("campaigns", plain.assembly.modules)
            self.assertIn("campaigns", plain.state.modules)
            self.assertIsNotNone(plain.view("armies"))


class AddModuleTests(OperationCase):
    MODS = {TEMPLE: (ADD, ())}

    @classmethod
    def prepare(cls):
        cls.reloaded = cls.game_over(cls.MODS)

    def test_the_game_has_the_module_its_state_and_its_view(self):
        self.assertIn(TEMPLE + ":temple", self.modded.assembly.modules)
        self.assertIn(TEMPLE + ":temple", self.modded.state.modules)
        self.assertEqual(self.modded.view(TEMPLE + ":visits")(), {"visits": 0, "names": []})

    def test_the_module_command_changes_its_state_and_its_view(self):
        game = self.game_over(self.MODS)
        self.assertEqual(game.view(TEMPLE + ":visits")(), {"visits": 0, "names": []})
        self.assertEqual(_agent_dispatch_inner(game, {}, {"cmd": TEMPLE + ":visit", "text": "ana"})["visits"], 1)
        self.assertEqual(game.view(TEMPLE + ":visits")(), {"visits": 1, "names": ["ana"]})

    def test_the_games_without_the_mod_have_neither_module_nor_command(self):
        for plain in self.plain_games():
            self.assertNotIn(TEMPLE + ":temple", plain.assembly.modules)
            self.assertNotIn(TEMPLE + ":temple", plain.state.modules)
            self.assertNotIn(TEMPLE + ":visit", command_registry.table_of(plain).commands)
            self.assertIs(_agent_dispatch_inner(plain, {}, {"cmd": TEMPLE + ":visit"})["ok"], False)
        self.assertIn(TEMPLE + ":visit", command_registry.table_of(self.modded).commands)
        self.assertNotIn(TEMPLE + ":visit", command_registry.COMMANDS)

    def test_the_modules_state_is_saved_and_loaded_with_the_game(self):
        game = self.game_over(self.MODS)
        _agent_dispatch_inner(game, {}, {"cmd": TEMPLE + ":visit", "text": "ana"})
        _agent_dispatch_inner(game, {}, {"cmd": TEMPLE + ":visit", "text": "bo"})
        path = os.path.join(self.tmp.name, "temple.json")
        save_state(game, path)
        load_state(self.reloaded, path)
        self.assertEqual(self.reloaded.view(TEMPLE + ":visits")(), {"visits": 2, "names": ["ana", "bo"]})
        self.assertEqual(self.reloaded.state.modules[TEMPLE + ":temple"].visits, 2)

    def test_a_save_with_the_module_is_refused_by_a_game_without_it(self):
        game = self.game_over(self.MODS)
        path = os.path.join(self.tmp.name, "temple_refused.json")
        save_state(game, path)
        with self.assertRaises(ValueError) as caught:
            load_state(self.after, path)
        self.assertEqual(caught.exception.args[0].cause, "save_module_set")


class ExtendModuleTests(OperationCase):
    MODS = {LAYER: (EXTEND, ())}

    def test_the_layer_overrides_the_method_and_super_reaches_the_shipped_one(self):
        answer = self.modded.view("store")[BASE_STORE]
        self.assertEqual(answer["layered_by"], LAYER)
        self.assertEqual(answer["shipped_keys"], ["default", "values"])
        self.assertEqual({key: answer[key] for key in ("default", "values")}, self.before.view("store")[BASE_STORE])

    def test_the_shipped_behaviour_under_the_layer_still_works(self):
        game = self.game_over(self.MODS)
        game.send(WriteStore(BASE_STORE, "tile_2", 7))
        self.assertEqual(game.view("store")[BASE_STORE]["values"], {"tile_2": 7})

    def test_a_method_outside_the_modules_declared_ones_is_labelled_unstable(self):
        self.assertEqual(self.modded.assembly.unstable, {"stores": [(LAYER, "helper")]})
        for plain in self.plain_games():
            self.assertEqual(plain.assembly.unstable, {})

    def test_the_games_without_the_layer_answer_as_shipped(self):
        for plain in self.plain_games():
            self.assertNotIn("layered_by", plain.view("store")[BASE_STORE])


class ExtendStackedTests(OperationCase):
    STACK = '''
class Layered:
    def store(self, name):
        answer = super().store(name)
        return dict(answer, layers=list(answer.get("layers", [])) + [MOD])


def register(api):
    api.extend_module("stores", Layered)
'''
    MODS = {ALPHA: (STACK, ()), BETA: (STACK, (ALPHA,))}

    def test_layers_stack_in_mod_load_order_each_reaching_the_one_below(self):
        self.assertEqual(self.modded.view("store")[BASE_STORE]["layers"], [ALPHA, BETA])

    def test_the_games_without_the_layers_have_none(self):
        for plain in self.plain_games():
            self.assertNotIn("layers", plain.view("store")[BASE_STORE])


class AdjustViewTests(OperationCase):
    MODS = {ALPHA: (ADJUST, ()), BETA: (ADJUST, (ALPHA,))}

    @classmethod
    def prepare(cls):
        cls.reversed_order = cls.game_over({ALPHA: (ADJUST, (BETA,)), BETA: (ADJUST, ())})

    def test_the_adjusted_answer_is_the_shipped_one_with_the_mods_changes(self):
        answer = self.modded.view("store")[BASE_STORE]
        self.assertEqual({key: answer[key] for key in ("default", "values")}, self.before.view("store")[BASE_STORE])
        self.assertIn("adjusted_by", answer)

    def test_stacked_adjusters_apply_in_mod_load_order(self):
        self.assertEqual(self.modded.view("store")[BASE_STORE]["adjusted_by"], [ALPHA, BASE_STORE, BETA, BASE_STORE])

    def test_the_other_load_order_gives_the_other_stacking(self):
        self.assertEqual(self.reversed_order.view("store")[BASE_STORE]["adjusted_by"], [BETA, BASE_STORE, ALPHA, BASE_STORE])

    def test_the_games_without_the_mods_are_not_adjusted(self):
        for plain in self.plain_games():
            self.assertNotIn("adjusted_by", plain.view("store")[BASE_STORE])


class ProvideTests(OperationCase):
    MODS = {GIVER: (PROVIDE, ())}

    def spawner_names(self, game):
        return [name for name, _spawner in game.assembly.modules["actors"].extensions().spawners]

    def test_the_mods_answer_joins_the_points_after_the_shipped_ones(self):
        names = self.spawner_names(self.modded)
        self.assertEqual(names[-1], GIVER + ":founding")
        self.assertEqual(names[:-1], self.spawner_names(self.before))

    def test_the_mods_hours_are_charged_in_its_game_only(self):
        self.assertEqual(self.modded.labour._world.director_overhead_hours(), 50.0)
        for plain in self.plain_games():
            self.assertEqual(plain.labour._world.director_overhead_hours(), 0.0)

    def test_the_games_without_the_mod_have_one_provider_fewer(self):
        for point in ("actor_spawners", "director_overhead"):
            self.assertEqual(len(self.modded.assembly.points[point].providers), len(self.before.assembly.points[point].providers) + 1)
            self.assertEqual(len(self.after.assembly.points[point].providers), len(self.before.assembly.points[point].providers))

    def test_providing_to_a_point_no_module_declares_is_refused_naming_the_mod(self):
        with self.assertRaises(AssemblyError) as caught:
            self.game_over({TAKER: ('def register(api):\n    api.provide("no_such_point", lambda: 1)\n', ())})
        self.assertIn(TAKER, str(caught.exception))   # presentation: the error text names the mod


class FigureAndCommandTests(OperationCase):
    MODS = {ALPHA: (FIGURE, ())}

    def test_the_mods_figure_is_read_and_listed_in_its_game_only(self):
        self.assertEqual(figures_of(self.modded)[ALPHA + ":mana"]["unit"], "mana")
        self.assertEqual(read_figure(self.modded, ALPHA + ":mana")["value"], 7.0)
        listed = _agent_dispatch_inner(self.modded, {}, {"cmd": "figures"})["figures"]
        self.assertIn(ALPHA + ":mana", [row["name"] for row in listed])
        for plain in self.plain_games():
            self.assertNotIn(ALPHA + ":mana", figures_of(plain))
            listed = _agent_dispatch_inner(plain, {}, {"cmd": "figures"})["figures"]
            self.assertNotIn(ALPHA + ":mana", [row["name"] for row in listed])

    def test_the_shipped_table_of_figures_is_not_touched(self):
        self.assertNotIn(ALPHA + ":mana", FIGURES)

    def test_two_mods_claiming_one_command_word_are_refused_naming_both(self):
        with self.assertRaises(ModError) as caught:
            self.game_over({ALPHA: (SAME_WORD, ()), BETA: (SAME_WORD, ())})
        self.assertIn(ALPHA, str(caught.exception))   # presentation: the error text names both mods
        self.assertIn(BETA, str(caught.exception))


class EffectsTests(OperationCase):
    MODS = {ALPHA: (EFFECTS, ())}

    def test_a_declared_effect_reaches_its_owner_through_the_mods_access(self):
        self.assertEqual(_agent_dispatch_inner(self.modded, {}, {"cmd": ALPHA + ":omen"})["kind"], ALPHA + ":omen")
        (event,) = self.modded.view("world_events")(ALPHA + ":omen")
        self.assertEqual(event["cause"], "a comet")

    def test_an_effect_the_mod_did_not_declare_is_refused_naming_the_mod_and_the_view(self):
        with self.assertRaises(UndeclaredRead) as caught:
            _agent_dispatch_inner(self.modded, {}, {"cmd": ALPHA + ":curse"})
        self.assertEqual((caught.exception.mod_id, caught.exception.view), (ALPHA, "cast"))


class WithdrawTests(OperationCase):
    MODS = {GIVER: (WITHDRAW, ())}

    def spawner_names(self, game):
        return [name for name, _spawner in game.assembly.modules["actors"].extensions().spawners]

    def test_the_shipped_provision_is_gone_and_the_mods_own_answer_remains(self):
        self.assertEqual(self.spawner_names(self.modded), [GIVER + ":only"])
        self.assertEqual(self.modded.assembly.applied.withdrawn, {"actors.spawners": GIVER})

    def test_the_games_without_the_mod_keep_every_shipped_spawner(self):
        for plain in self.plain_games():
            self.assertIn("firm_entry", self.spawner_names(plain))
            self.assertEqual(plain.assembly.applied.withdrawn, {})

    def test_withdrawing_a_provision_no_module_makes_is_refused_naming_the_mod(self):
        with self.assertRaises(AssemblyError) as caught:
            self.game_over({TAKER: ('def register(api):\n    api.withdraw("actors.nothing")\n', ())})
        self.assertIn(TAKER, str(caught.exception))   # presentation: the error text names the mod


if __name__ == "__main__":
    unittest.main()
