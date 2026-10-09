"""A mod brings a kind of actor as data (a declared species) or as consented code, through the ordinary rules."""

QUICK_TOPIC = True

import json
import unittest

from sim.agents import registry as registry_module
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, register_declared_kinds
from sim.agents.declared_kind import DeclaredKind
from sim.engine import mod_code
from sim.engine.actor_kinds_data import load_kind_declarations
from sim.engine.data import ROOT
from sim.engine.mods import ModError
from sim.tests.agents_fake_world import FakeWorld
from sim.tests.test_mod_removal_and_civs import ModTestBase

ACME = "test_acme_k3f9"
KIND = ACME + ":elf"
DECLARATION = {"needs": {"food": 1.0}, "birth_rate": 0.04, "death_rate": 0.02, "famine_death_rate": 0.3,
               "trade": "labourer"}


class ElfWorld(FakeWorld):
    def __init__(self, pay=200.0, food=100.0):
        super().__init__()
        self.pay, self.food = pay, food

    def need_floor_costs_per_person_year(self):
        return {"food": self.food}

    def pay_per_person_year(self, trade):
        return self.pay


class KindTestBase(ModTestBase):
    def tearDown(self):
        registry_module.ACTOR_CLASSES.pop(KIND, None)
        registry_module.ACTOR_CLASSES.pop(ACME + ":golem", None)
        mod_code.LOADED.clear()
        mod_code.COMMAND_REGISTRATIONS.clear()
        super().tearDown()

    def write_kinds(self, kinds):
        self.add_mod(ACME)
        path = self.mods_dir / ACME / "data" / "world" / "actor_kinds.json"
        path.write_text(json.dumps({"kinds": kinds}))

    def declarations(self):
        return load_kind_declarations(ROOT, str(self.mods_dir))


class DeclaredKindTests(KindTestBase):
    def species(self, world, members=1000.0):
        register_declared_kinds({KIND: DECLARATION})
        registry = ActorRegistry(ActorsState(home_country="home"))
        actor = registry.add("elf:one", ActorRecord(kind=KIND, name="elves", members=members, money=0.0))
        return actor, world

    def test_a_declared_kind_is_registered_and_built_from_the_registry(self):
        actor, _world = self.species(ElfWorld())
        self.assertIsInstance(actor, DeclaredKind)
        self.assertEqual(actor.kind, KIND)

    def test_a_fed_species_grows_by_its_declared_rates(self):
        actor, world = self.species(ElfWorld(pay=300.0))
        actor.advance(world)
        self.assertAlmostEqual(actor.record.members, 1000.0 * (1 + 0.04 - 0.02), places=6)
        self.assertEqual(actor.record.shortfall, {"food": 0.0})

    def test_a_starved_species_shrinks_and_competes_for_the_same_food(self):
        actor, world = self.species(ElfWorld(pay=10.0, food=100.0))
        actor.advance(world)
        self.assertGreater(actor.record.shortfall["food"], 0.5)
        self.assertLess(actor.record.members, 1000.0)

    def test_money_moves_only_through_the_ledger_and_is_conserved(self):
        actor, world = self.species(ElfWorld(pay=150.0))
        actor.advance(world)
        edge_income = sum(value for label, value in actor.record.income.items() if label.startswith("edge:"))
        edge_outlay = sum(value for label, value in actor.record.outlays.items() if label.startswith("edge:"))
        self.assertAlmostEqual(actor.money, edge_income - edge_outlay)
        self.assertGreater(edge_income, 0.0)

    def test_declaration_is_loaded_from_a_mod_and_checked(self):
        self.write_kinds({KIND: DECLARATION})
        self.assertEqual(self.declarations()[KIND]["birth_rate"], 0.04)

    def test_unknown_need_is_refused(self):
        self.write_kinds({KIND: dict(DECLARATION, needs={"mana_dust": 1.0})})
        with self.assertRaises(ModError) as caught:
            self.declarations()
        self.assertIn("mana_dust", str(caught.exception))

    def test_missing_rate_is_refused(self):
        self.write_kinds({KIND: {key: value for key, value in DECLARATION.items() if key != "death_rate"}})
        with self.assertRaises(ModError):
            self.declarations()

    def test_kind_outside_the_namespace_is_refused(self):
        self.write_kinds({"elf": DECLARATION})
        with self.assertRaises(ModError):
            self.declarations()

    def test_a_mod_kind_with_a_new_need_uses_the_mods_own_need(self):
        self.write_kinds({KIND: dict(DECLARATION, needs={"food": 1.0, ACME + ":mana": 0.5})})
        (self.mods_dir / ACME / "data" / "world" / "needs.json").write_text(json.dumps(
            {"needs": {ACME + ":mana": {"surplus_budget_share": 0.1}}}))
        self.assertIn(ACME + ":mana", self.declarations()[KIND]["needs"])

    def test_a_record_of_a_missing_mod_kind_names_the_mod(self):
        state = ActorsState(home_country="home")
        state.records["x"] = ActorRecord(kind="gone_mod_k3f9:dragon")
        with self.assertRaises(ValueError) as caught:
            ActorRegistry(state)
        self.assertIn("gone_mod_k3f9", str(caught.exception))


CODE = '''
from sim.agents.api import RecordedActor

class Golem(RecordedActor):
    kind = "golem"
    def advance(self, world):
        self.record.members += 1

def register(api):
    api.actor_kind("golem", Golem)
'''


class CodeKindTests(KindTestBase):
    def test_consented_code_registers_a_prefixed_kind(self):
        self.add_mod(ACME)
        folder = self.mods_dir / ACME
        (folder / "golem.py").write_text(CODE)
        manifest = json.loads((folder / "mod.json").read_text())
        manifest.update(code=["golem.py"], permissions=["code"])
        (folder / "mod.json").write_text(json.dumps(manifest))
        mod_code.run_mod_code(str(self.mods_dir))
        self.assertNotIn(ACME + ":golem", registry_module.ACTOR_CLASSES)
        mod_code.allow(str(self.mods_dir), ACME)
        mod_code.run_mod_code(str(self.mods_dir))
        self.assertIn(ACME + ":golem", registry_module.ACTOR_CLASSES)
        self.assertNotIn("golem", registry_module.ACTOR_CLASSES)


if __name__ == "__main__":
    unittest.main()
