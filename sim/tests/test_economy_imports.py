"""The economy package stays standalone: it imports sim.world, sim.constants and itself, never sim.engine,
and only sim/engine/economy_port.py imports it from the engine."""
import ast
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ECONOMY_DIR = os.path.join(ROOT, "sim", "economy")
ENGINE_DIR = os.path.join(ROOT, "sim", "engine")
ALLOWED_ENGINE_IMPORTERS = {"economy_port.py"}


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


if __name__ == "__main__":
    unittest.main()
