"""Import and content walls of the labour package and the labour-market core."""
import ast
import glob
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LABOUR_DIR = os.path.join(ROOT, "sim", "labour")
MARKET_DIR = os.path.join(LABOUR_DIR, "market")

# Existing engine imports in sim/labour, pinned so new ones fail (Complaints/404 removes them).
KNOWN_VIOLATIONS = {
    ("sim/labour/wage_provider.py", "sim.engine.solve_prices_core"),
    ("sim/labour/workforce_spinup.py", "sim.engine.solve_prices_core"),
}


def python_files(directory):
    for folder, _subfolders, filenames in os.walk(directory):
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                yield os.path.join(folder, filename)


def imports_of(path):
    """(module, level) for every import; plain `import a.b` has level 0."""
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((alias.name, 0) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.append((node.module or "", node.level))
    return found


def docstring_nodes(tree):
    skipped = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                skipped.add(id(body[0].value))
    return skipped


class LabourWallTests(unittest.TestCase):
    def test_labour_never_imports_engine_or_ui_beyond_known_violations(self):
        found = set()
        for path in python_files(LABOUR_DIR):
            relative = os.path.relpath(path, ROOT).replace(os.sep, "/")
            for module, level in imports_of(path):
                if level == 0 and any(module == wall or module.startswith(wall + ".")
                                      for wall in ("sim.engine", "sim.ui")):
                    found.add((relative, module))
        self.assertEqual(found - KNOWN_VIOLATIONS, set(), "new engine/ui imports in sim/labour")
        self.assertEqual(KNOWN_VIOLATIONS - found, set(), "known violation fixed: remove it from the set")

    def test_market_core_imports_only_standard_library_constants_and_itself(self):
        standard = set(sys.stdlib_module_names)
        for path in python_files(MARKET_DIR):
            for module, level in imports_of(path):
                if level > 0:
                    self.assertEqual(level, 1, "%s: relative import leaves the core" % path)
                    continue
                root = module.split(".")[0]
                allowed = root in standard or module == "sim.constants"
                self.assertTrue(allowed, "%s imports %s" % (os.path.relpath(path, ROOT), module))

    def test_market_core_names_no_trade_or_civilisation(self):
        with open(os.path.join(ROOT, "data", "world", "trades.json"), encoding="utf-8") as handle:
            forbidden = set(json.load(handle)["trades"])
        for path in glob.glob(os.path.join(ROOT, "data", "civilizations", "*.json")):
            forbidden.add(os.path.splitext(os.path.basename(path))[0])
        for path in python_files(MARKET_DIR):
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
            skipped = docstring_nodes(tree)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skipped:
                    self.assertNotIn(node.value, forbidden, "%s names a content id" % os.path.relpath(path, ROOT))


if __name__ == "__main__":
    unittest.main()
