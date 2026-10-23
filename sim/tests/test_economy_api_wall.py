"""sim/economy/api.py publishes every name the rest of the program takes from sim.economy (a static scan). Its accessors
agree with reading the record directly: test_economy_api.py."""
QUICK_TOPIC = True
import ast
import os
import unittest

from sim.economy import api

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKIPPED_DIRS = {os.path.join(ROOT, "sim", "economy"), os.path.join(ROOT, "sim", "tests")}


def python_files():
    for folder, subfolders, filenames in os.walk(ROOT):
        subfolders[:] = [name for name in subfolders if not name.startswith(".") and name != "__pycache__"
                         and os.path.join(folder, name) not in SKIPPED_DIRS]
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                yield os.path.join(folder, filename)


def economy_imports(path):
    """(module, name) for each `from sim.economy[.x] import name`; name is None for `import sim.economy.x`."""
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module \
                and (node.module == "sim.economy" or node.module.startswith("sim.economy.")):
            for alias in node.names:
                yield node.module, alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "sim.economy" or alias.name.startswith("sim.economy."):
                    yield alias.name, None


class EconomyApiTests(unittest.TestCase):
    def test_the_wall_is_two_way(self):
        self.assertEqual(api.WALL, "two-way")

    def test_every_outside_import_is_published(self):
        found = 0
        for path in python_files():
            for module, name in economy_imports(path):
                if name == "api":
                    continue
                found += 1
                where = "%s imports %s from %s" % (os.path.relpath(path, ROOT), name, module)
                self.assertIsNotNone(name, where)
                self.assertTrue(hasattr(api, name), where)
        self.assertGreater(found, 0)

if __name__ == "__main__":
    unittest.main()
