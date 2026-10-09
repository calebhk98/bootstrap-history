"""The economy package stays standalone: it imports sim.world, sim.constants and itself, never sim.engine,
and only the port (sim/engine/economy_port*.py) imports it from the engine."""
import ast
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ECONOMY_DIR = os.path.join(ROOT, "sim", "economy")
ENGINE_DIR = os.path.join(ROOT, "sim", "engine")
ALLOWED_ENGINE_IMPORTERS = {"economy_port.py", "economy_port_setup.py", "economy_port_year.py", "economy_port_cargo.py",
                           "economy_port_health.py", "economy_port_sites.py", "economy_port_country.py"}


def imported_modules(path):
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module


def python_files(directory):
    for folder, _subfolders, filenames in os.walk(directory):
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                yield os.path.join(folder, filename)


class EconomyImportTests(unittest.TestCase):
    def test_the_economy_never_imports_the_engine(self):
        for path in python_files(ECONOMY_DIR):
            for module in imported_modules(path):
                self.assertFalse(module == "sim.engine" or module.startswith("sim.engine."),
                                 "%s imports %s" % (os.path.relpath(path, ROOT), module))

    def test_only_the_port_imports_the_economy_from_the_engine(self):
        for path in python_files(ENGINE_DIR):
            if os.path.basename(path) in ALLOWED_ENGINE_IMPORTERS:
                continue
            for module in imported_modules(path):
                self.assertFalse(module == "sim.economy" or module.startswith("sim.economy."),
                                 "%s imports %s" % (os.path.relpath(path, ROOT), module))

    def test_the_port_imports_only_the_economy_surface(self):
        for name in sorted(ALLOWED_ENGINE_IMPORTERS):
            path = os.path.join(ENGINE_DIR, name)
            for module in imported_modules(path):
                if module.startswith("sim.economy."):
                    self.assertEqual(module, "sim.economy.api", "%s imports %s" % (name, module))
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "sim.economy" and node.level == 0:
                    self.assertEqual([alias.name for alias in node.names], ["api"], "%s imports past the surface" % name)

    def test_the_port_does_not_read_the_record(self):
        for name in sorted(ALLOWED_ENGINE_IMPORTERS):
            with open(os.path.join(ENGINE_DIR, name), encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            for node in ast.walk(tree):
                if not isinstance(node, ast.Attribute) or node.attr != "record":
                    continue
                treasury = isinstance(node.value, ast.Call) and getattr(node.value.func, "attr", "") == "state_treasury"
                self.assertTrue(treasury, "%s reads .record at line %d" % (name, node.lineno))


if __name__ == "__main__":
    unittest.main()
