"""The persistent price-solve cache: its key covers every input, a cold cache
gives the same answer as a warm one, and a warm cache skips the solver.

sim/engine/solve_cache.py: on-disk cache keyed on a hash of every solve input.
"""
import copy
import os
import shutil
import tempfile
import unittest

from sim.engine import prices as engine_prices, solve_cache

_WAGES = {"labourer": 1.0, "smith": 2.0}


def _inputs(**changes):
    inputs = {"production": {"iron_kg": {"outputs": {"iron_kg": 1000.0},
                                         "inputs": {}, "labour_hours": {"labourer": 5.0}}},
              "gates": ["node_a"], "civilization": "rome_100ad",
              "wage_ratios": dict(_WAGES)}
    inputs.update(changes)
    return inputs


class SolveKeyTests(unittest.TestCase):
    def test_key_is_stable(self):
        self.assertEqual(solve_cache.solve_key(_inputs()), solve_cache.solve_key(_inputs()))

    def test_key_changes_with_each_input(self):
        base = solve_cache.solve_key(_inputs())
        changed_production = _inputs()
        changed_production["production"]["iron_kg"]["labour_hours"]["labourer"] = 6.0
        variants = {
            "production": changed_production,
            "gates": _inputs(gates=["node_a", "node_b"]),
            "civilization": _inputs(civilization="china_100ad"),
            "wages": _inputs(wage_ratios={"labourer": 1.0, "smith": 2.5}),
        }
        for name, variant in variants.items():
            self.assertNotEqual(base, solve_cache.solve_key(variant), name)

    def test_key_changes_with_data_files_tree_and_source(self):
        root = tempfile.mkdtemp(prefix="solve_cache_env_")
        original_root = solve_cache._ROOT
        try:
            for relative in ("data/production/a.json", "data/tech_tree.json",
                             "data/civilizations/rome_100ad.json", "data/wages.json",
                             "mods/m.json", "sim/solver.py"):
                path = os.path.join(root, relative)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as handle:
                    handle.write("1")
            solve_cache._ROOT = root
            for relative in ("data/production/a.json", "data/tech_tree.json",
                             "data/civilizations/rome_100ad.json", "data/wages.json",
                             "mods/m.json", "sim/solver.py"):
                solve_cache.forget_environment_digest()
                before = solve_cache.solve_key(_inputs())
                with open(os.path.join(root, relative), "w") as handle:
                    handle.write("2")
                solve_cache.forget_environment_digest()
                self.assertNotEqual(before, solve_cache.solve_key(_inputs()), relative)
        finally:
            solve_cache._ROOT = original_root
            solve_cache.forget_environment_digest()
            shutil.rmtree(root, ignore_errors=True)


class ColdWarmTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="solve_cache_dir_")
        self.original_directory = solve_cache.DEFAULT_CACHE_DIRECTORY
        solve_cache.DEFAULT_CACHE_DIRECTORY = self.directory
        self.original_solve = engine_prices.solve_prices.solve
        self.solver_calls = 0

        def counting_solve(*arguments, **keywords):
            self.solver_calls += 1
            return self.original_solve(*arguments, **keywords)
        engine_prices.solve_prices.solve = counting_solve
        engine_prices.reset_caches_for_tests()

    def tearDown(self):
        engine_prices.solve_prices.solve = self.original_solve
        solve_cache.DEFAULT_CACHE_DIRECTORY = self.original_directory
        shutil.rmtree(self.directory, ignore_errors=True)
        engine_prices.reset_caches_for_tests()

    def _solve(self):
        engine_prices.reset_caches_for_tests()
        engine_prices._default_production_entries()
        document = {"wage_rates_denarii_per_hour": {"labourer": {"rate": 2.0}},
                    "money_per_labour_hour": 2.0}
        return engine_prices.solved_prices([], document)

    def test_cold_equals_warm_and_warm_skips_solver(self):
        cold = self._solve()
        cold_calls = self.solver_calls
        self.assertEqual(cold_calls, 1)
        warm = self._solve()
        self.assertEqual(self.solver_calls, cold_calls)
        for field in ("prices_in_labour_hours", "resolvable_materials",
                      "chosen_recipe_by_material", "converged", "iterations_run",
                      "gate_nodes_held", "civilization_id"):
            self.assertEqual(getattr(cold, field), getattr(warm, field), field)

    def test_deleted_cache_gives_same_result(self):
        first = self._solve()
        shutil.rmtree(self.directory)
        second = self._solve()
        self.assertEqual(first.prices_in_labour_hours, second.prices_in_labour_hours)
        self.assertEqual(self.solver_calls, 2)

    def test_unwritable_cache_is_not_required(self):
        solve_cache.DEFAULT_CACHE_DIRECTORY = os.path.join(self.directory, "file", "sub")
        with open(os.path.join(self.directory, "file"), "w") as handle:
            handle.write("x")
        self.assertTrue(self._solve().prices_in_labour_hours)


_IMPORT_PROBE = (
    "import sys, warnings; warnings.simplefilter('ignore'); sys.path.insert(0, %r)\n"
    "from sim import solve_prices\n"
    "original, calls = solve_prices.solve, []\n"
    "solve_prices.solve = lambda *a, **k: (calls.append(1), original(*a, **k))[1]\n"
    "import sim.simulator\n"
    "print(len(calls))\n")


class ImportSolveCountTests(unittest.TestCase):
    def test_warm_import_runs_no_solver(self):
        import subprocess
        import sys
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        command = [sys.executable, "-c", _IMPORT_PROBE % root]
        subprocess.run(command, check=True, capture_output=True, cwd=root)
        warm = subprocess.run(command, check=True, capture_output=True, text=True, cwd=root)
        self.assertEqual(warm.stdout.strip(), "0")


if __name__ == "__main__":
    unittest.main()
