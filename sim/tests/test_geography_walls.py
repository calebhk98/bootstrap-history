"""The geography package's walls: outside code reaches it only through its api, and it reaches
nothing above it (engine, ui, economy, labour, agents). Its reads of sim.world are an allowlist
that only shrinks."""
import ast
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEOGRAPHY_DIR = os.path.join(ROOT, "sim", "geography")
FORBIDDEN_PACKAGES = ("sim.engine", "sim.ui", "sim.economy", "sim.labour", "sim.agents")
# file -> sim.world modules it still reads; remove entries as the dependency is turned around
WORLD_IMPORTS_ALLOWED = {}


def imported_modules(path):
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module in ("sim", "sim.world"):
                for alias in node.names:
                    yield "%s.%s" % (node.module, alias.name)
            else:
                yield node.module


def python_files(directory):
    for folder, _subfolders, filenames in os.walk(directory):
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                yield os.path.join(folder, filename)


def under(module, package):
    return module == package or module.startswith(package + ".")


class GeographyWallTests(unittest.TestCase):
    def test_geography_never_imports_the_layers_above_it(self):
        for path in python_files(GEOGRAPHY_DIR):
            for module in imported_modules(path):
                self.assertFalse(any(under(module, package) for package in FORBIDDEN_PACKAGES),
                                 "%s imports %s" % (os.path.relpath(path, ROOT), module))

    def test_geography_reads_sim_world_only_where_allowed(self):
        for path in python_files(GEOGRAPHY_DIR):
            allowed = WORLD_IMPORTS_ALLOWED.get(os.path.basename(path), set())
            for module in imported_modules(path):
                if under(module, "sim.world"):
                    self.assertIn(module, allowed, "%s imports %s" % (os.path.relpath(path, ROOT), module))

    def test_game_code_outside_the_package_uses_only_the_api(self):
        for package in ("engine", "ui", "economy", "labour", "agents", "world"):
            for path in python_files(os.path.join(ROOT, "sim", package)):
                for module in imported_modules(path):
                    if under(module, "sim.geography"):
                        self.assertEqual(module, "sim.geography.api",
                                         "%s imports %s" % (os.path.relpath(path, ROOT), module))


if __name__ == "__main__":
    unittest.main()
