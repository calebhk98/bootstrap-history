"""SMOKE: two games in one process run the mods of their own mod set. A mod with consented code gives an actor kind, a store, a
year phase, a directed-hours overhead and a wealth claim; the game built over its mods directory has them all, the game built
before and the game built after, over the shipped mods alone, have none, and the first game still has them. Nothing a mod
registers is kept in a process global: each registry is an extension point of the module that owns it
(docs/architecture/MODULE_REGISTRY_PLAN.md section 4.5). The rules are tested one function at a time in test_externalities,
test_town_providers, test_year_phases, test_mod_stores and test_mod_actor_kinds."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from sim.engine import bridge_land, mod_code, year_phases
from sim.stores.api import WriteStore
from sim.tests.harness import unopened_sim

ACME = "test_acme_s7q2"
CODE = '''
from sim.agents.api import RecordedActor


class Golem(RecordedActor):
    kind = "golem"


def register(api):
    api.actor_kind("golem", Golem)
    api.store("mana", keyed_by="tile", default=0.0, unit="mana")
    api.phase("tick", "world", lambda sim, seats: None, after="market")
    api.director_overhead(lambda sim: 120.0)
    api.provide("wealth_claims", lambda: (lambda sim: 5.0, lambda sim, amount, taker: 0.0))
'''


def write_mod(mods_dir: Path) -> None:
    folder = mods_dir / ACME
    (folder / "data").mkdir(parents=True)
    (folder / "mod.json").write_text(json.dumps({"id": ACME, "name": ACME, "version": "1", "dependencies": [], "conflicts": [],
                                                 "code": ["hooks.py"], "permissions": ["code"]}))
    (folder / "hooks.py").write_text(CODE)
    mod_code.allow(str(mods_dir), ACME)


class TwoGamesTwoModSetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        mods_dir = Path(cls.tmp.name) / "mods"
        write_mod(mods_dir)
        cls.before = unopened_sim()
        with mock.patch.object(bridge_land, "MODS_DIR", str(mods_dir)):
            cls.modded = unopened_sim()
        cls.after = unopened_sim()

    @classmethod
    def tearDownClass(cls):
        mod_code.LOADED.clear()
        mod_code.MOD_OPERATIONS.clear()
        cls.tmp.cleanup()

    def kinds(self, game):
        return sorted(kind for answer in game.assembly.points["actor_kinds"]() for kind in answer)

    def test_the_game_over_the_mods_directory_has_the_mods_actor_kind_and_the_others_do_not(self):
        self.assertIn(ACME + ":golem", self.kinds(self.modded))
        self.assertNotIn(ACME + ":golem", self.kinds(self.before))
        self.assertNotIn(ACME + ":golem", self.kinds(self.after))

    def test_the_mods_store_is_declared_in_its_game_only(self):
        self.modded.send(WriteStore(ACME + ":mana", "tile_1", 4.0, ACME))
        self.assertEqual(self.modded.stores.view(ACME + ":mana").get("tile_1"), 4.0)
        self.assertNotIn(ACME + ":mana", self.before.stores.declared())
        self.assertNotIn(ACME + ":mana", self.after.stores.declared())

    def test_the_mods_phase_is_placed_in_its_game_only(self):
        placed = [phase.name for phase in year_phases.ordered_phases(self.modded.assembly.applied.phases)]
        self.assertEqual(placed[placed.index("market") + 1], ACME + ":tick")
        for plain in (self.before, self.after):
            self.assertEqual(plain.assembly.applied.phases, [])

    def test_the_mods_overhead_and_claim_are_answers_of_its_game_only(self):
        self.assertEqual(self.modded.labour._world.director_overhead_hours(), 120.0)
        self.assertEqual(len(self.modded.assembly.points["wealth_claims"]()), 1)
        for plain in (self.before, self.after):
            self.assertEqual(plain.labour._world.director_overhead_hours(), 0.0)
            self.assertEqual(plain.assembly.points["wealth_claims"](), [])


if __name__ == "__main__":
    unittest.main()
