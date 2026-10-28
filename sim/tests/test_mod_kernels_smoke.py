"""SMOKE: a consented code mod replaces a kernel (Complaint 661) in a whole game. An equal implementation is accepted and the
year's labour market calls it; a wrong one is refused naming the mod and the kernel; two mods replacing one kernel are refused
naming both; a save written under a replacement is refused by a game without it. The rules are tested one function at a time in
test_assembly_kernels, test_kernel_fetch_wage and test_kernel_least_cost_tree."""
import itertools
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from sim.assembly.api import AssemblyError
from sim.engine import bridge_land, mod_code
from sim.engine.saveload import load_state, save_state
from sim.tests.harness import sim, unopened_sim
from sim.tests.test_mod_operations_smoke import write_mod

EQUAL_WAGE, EQUAL_TREE, WRONG, OTHER_WRONG = "test_equalwage_k4m1", "test_equaltree_k4m1", "test_wrong_k4m1", "test_second_k4m1"

DIRECTORIES = itertools.count()
USED = {"fetch_wage": 0, "least_cost_tree": 0}

WAGE_MOD = '''
from sim.labour.market.fetch_wage import fetch_wage as reference
from sim.tests.test_mod_kernels_smoke import USED


def same_answer(*arguments, **keywords):
    USED["fetch_wage"] += 1
    return reference(*arguments, **keywords)


def register(api):
    api.kernel("markets.fetch_wage", same_answer)
'''

TREE_MOD = '''
from sim.geography.routes_cost_tree import least_cost_tree as reference
from sim.tests.test_mod_kernels_smoke import USED


def same_answer(*arguments, **keywords):
    USED["least_cost_tree"] += 1
    return reference(*arguments, **keywords)


def register(api):
    api.kernel("markets.least_cost_tree", same_answer)
'''

WRONG_MOD = '''
from sim.labour.market.fetch_wage import fetch_wage as reference


def a_cent_off(*arguments, **keywords):
    found = reference(*arguments, **keywords)
    return None if found is None else found + 0.01


def register(api):
    api.kernel("markets.fetch_wage", a_cent_off)
'''


class KernelCase(unittest.TestCase):
    tmp = None

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        mod_code.LOADED.clear()
        mod_code.MOD_OPERATIONS.clear()
        cls.tmp.cleanup()

    def game_over(self, mods, build=unopened_sim):
        """A game built with these mods (id -> source) installed and consented to."""
        mods_dir = Path(self.tmp.name) / ("mods_%d" % next(DIRECTORIES))
        for mod_id, source in mods.items():
            write_mod(mods_dir, mod_id, source)
        for mod_id in mods:
            mod_code.allow(str(mods_dir), mod_id)
        with mock.patch.object(bridge_land, "MODS_DIR", str(mods_dir)):
            return build()


class AnEqualKernelInAWholeGame(KernelCase):
    """One game built over two mods, each replacing a kernel with an equal implementation, and stepped a year."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        USED["fetch_wage"] = 0
        cls.game = cls().game_over({EQUAL_WAGE: WAGE_MOD, EQUAL_TREE: TREE_MOD}, build=sim)
        cls.game.step()

    def test_the_game_records_both_replacements(self):
        self.assertEqual(self.game.state.assembly_record["kernels"], {"markets.fetch_wage": EQUAL_WAGE, "markets.least_cost_tree": EQUAL_TREE})

    def test_the_labour_market_of_a_year_calls_the_replacement(self):
        self.assertEqual(self.game.assembly.modules["markets"].kernel("markets.fetch_wage").__name__, "same_answer")
        self.assertGreater(USED["fetch_wage"], 0)

    def test_the_economys_carriage_table_is_handed_the_replacement_of_the_route_search(self):
        self.assertEqual(self.game.economy.agent._economy.carriage.cost_tree.__name__, "same_answer")

    def test_a_game_without_the_mods_runs_the_references_and_records_no_replacement(self):
        game = unopened_sim()
        self.assertEqual(game.state.assembly_record["kernels"], {})
        self.assertEqual(game.assembly.modules["markets"].kernel("markets.fetch_wage").__name__, "fetch_wage")
        self.assertEqual(game.assembly.modules["markets"].kernel("markets.least_cost_tree").__name__, "least_cost_tree")

    def test_a_save_written_under_the_replacements_is_refused_by_a_game_without_them(self):
        path = os.path.join(self.tmp.name, "kernel_save.json")
        save_state(self.game, path)
        with self.assertRaises(ValueError) as caught:
            load_state(unopened_sim(), path)
        self.assertEqual(caught.exception.args[0].cause, "save_module_set")
        self.assertIn("markets.fetch_wage", str(caught.exception.args[0]))   # presentation: the refusal names the kernel


class AWrongKernelInAWholeGame(KernelCase):

    def test_a_wrong_replacement_is_refused_naming_the_mod_and_the_kernel(self):
        with self.assertRaises(AssemblyError) as caught:
            self.game_over({WRONG: WRONG_MOD})
        self.assertIn(WRONG, str(caught.exception))   # presentation: the error names the mod and the kernel
        self.assertIn("markets.fetch_wage", str(caught.exception))

    def test_two_mods_replacing_one_kernel_are_refused_naming_both(self):
        with self.assertRaises(AssemblyError) as caught:
            self.game_over({EQUAL_WAGE: WAGE_MOD, OTHER_WRONG: WAGE_MOD})
        self.assertIn(EQUAL_WAGE, str(caught.exception))   # presentation: the error names both mods and the kernel
        self.assertIn(OTHER_WRONG, str(caught.exception))
        self.assertIn("markets.fetch_wage", str(caught.exception))

    def test_the_game_after_a_refusal_is_built_as_shipped(self):
        game = unopened_sim()
        self.assertEqual(game.state.assembly_record["kernels"], {})


if __name__ == "__main__":
    unittest.main()
