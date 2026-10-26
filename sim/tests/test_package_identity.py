"""Canonical package identity (sim is the one root): every repository module sits in `sys.modules` under one name, only under
`sim.*`, with no bare `constants`, `engine`, `world`, `simulator` or `data`, and the shared registry and classes have one identity.
Imports the supported entry points in this process and inspects `sys.modules`; no subprocess. The suite runs from a checkout of
any name, in any directory."""
import importlib
import os
import sys
import unittest

import sim.constants
import sim.engine.core
import sim.engine.state
import sim.simulator
from sim.engine.data import ROOT

QUICK_TOPIC = True

BARE_NAMES = ("constants", "engine", "world", "simulator", "data")
ENTRY_POINTS = ("sim.simulator", "sim.engine.validate_production", "sim.prices.solve_prices", "sim.tests.fingerprint")
CANONICAL = ("sim.constants", "sim.engine.core", "sim.world.demography", "sim.engine.saveload")


def repository_modules():
    """{real path: [names it is imported under]} for every module whose file is inside the repository."""
    root = os.path.realpath(os.path.normcase(ROOT))
    by_file = {}
    for name, module in list(sys.modules.items()):
        file = getattr(module, "__file__", None)
        if module is None or not file or name == "__main__":
            continue
        real = os.path.realpath(os.path.normcase(file))
        if real.startswith(root):
            by_file.setdefault(real, []).append(name)
    return by_file


class PackageIdentityTests(unittest.TestCase):
    def test_no_bare_module_name_is_imported(self):
        self.assertEqual([name for name in BARE_NAMES if name in sys.modules], [])

    def test_the_core_modules_are_imported_under_sim(self):
        for name in CANONICAL:
            importlib.import_module(name)
        self.assertEqual([name for name in CANONICAL if name not in sys.modules], [])

    def test_the_entry_points_import_cleanly_under_one_name_each(self):
        for name in ENTRY_POINTS:
            importlib.import_module(name)
        self.assertEqual({path: names for path, names in repository_modules().items() if len(names) > 1}, {})
        self.assertEqual([name for name in BARE_NAMES if name in sys.modules], [])

    def test_the_sim_directory_is_not_on_the_import_path(self):
        here = os.path.normcase(os.path.abspath(os.path.dirname(sim.simulator.__file__)))
        self.assertEqual([entry for entry in sys.path if os.path.normcase(os.path.abspath(entry)) == here], [])

    def test_the_constants_registry_and_the_game_classes_have_one_identity(self):
        self.assertIsInstance(sim.constants.REGISTRY, dict)
        self.assertTrue(sim.constants.REGISTRY)
        self.assertIs(sim.simulator.Sim, sim.engine.core.Sim)
        for name in ("SimulationState", "ActiveProjectState"):
            self.assertIs(getattr(sim.engine.core, name), getattr(sim.engine.state, name))


if __name__ == "__main__":
    unittest.main()
