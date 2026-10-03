"""Walled packages are reached only through their surface.

A package is walled when it has an `api.py`: every `sim/<name>/api.py` is found, never listed.
Outside such a package (tests aside, which may test internals), code imports only
`sim.<name>.api`, reads none of the package's private names, and calls the methods its mixins
put on `Sim` through the package's port (`sim.<name>.<method>`), not straight off `Sim`; the port
itself is the mixin property named after the package.
`sim/economy/` has its own wall (sim/tests/test_economy_imports.py) and is skipped here.
Design: docs/architecture/PACKAGE_WALLS.md.
"""
import ast
import os
import unittest

from .source_dirs import engine_side_dirs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SIM_DIR = os.path.join(ROOT, "sim")
TESTS_DIR = os.path.join(SIM_DIR, "tests")
SKIPPED_PACKAGES = {"economy"}


def walled_packages():
    for name in sorted(os.listdir(SIM_DIR)):
        if name not in SKIPPED_PACKAGES and os.path.isfile(os.path.join(SIM_DIR, name, "api.py")):
            yield name


def python_files(directory):
    for folder, subfolders, filenames in os.walk(directory):
        subfolders[:] = [sub for sub in subfolders if sub != "__pycache__"]
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                yield os.path.join(folder, filename)


def parse(path):
    with open(path, encoding="utf-8") as handle:
        return ast.parse(handle.read(), filename=path)


def module_of(path):
    relative = os.path.relpath(path, ROOT)[:-len(".py")].replace(os.sep, ".")
    return relative[:-len(".__init__")] if relative.endswith(".__init__") else relative


def imported_modules(path, tree):
    """Absolute names of every module a file imports, relative imports resolved; a
    `from package import name` also yields `package.name`, since the name may be a module."""
    package = module_of(path) if path.endswith("__init__.py") else module_of(path).rpartition(".")[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package.split(".")
                base = ".".join(parts[:len(parts) - (node.level - 1)])
                module = base + ("." + node.module if node.module else "")
            else:
                module = node.module or ""
            yield module
            for alias in node.names:
                yield module + "." + alias.name


def wall_kind(package):
    """The package's `WALL` declaration in its api.py ("two-way" once it no longer reaches the engine)."""
    for node in parse(os.path.join(SIM_DIR, package, "api.py")).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "WALL" for t in node.targets):
            return node.value.value
    return "one-way"


def sim_base_modules():
    """The module each base class of `class Sim` (sim/engine/core.py) is imported from."""
    path = os.path.join(SIM_DIR, "engine", "core.py")
    tree = parse(path)
    imported_from = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = "sim.engine" + ("." + module if module else "")
            for alias in node.names:
                imported_from[alias.asname or alias.name] = module
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Sim":
            return [imported_from.get(base.id, "sim.engine.core") for base in node.bases if isinstance(base, ast.Name)]
    return []


def outside_files(package):
    package_dir = os.path.join(SIM_DIR, package)
    for path in python_files(SIM_DIR):
        if path.startswith(package_dir + os.sep) or path.startswith(TESTS_DIR + os.sep):
            continue
        if path.startswith(os.path.join(SIM_DIR, "economy") + os.sep):
            continue
        yield path


def defined_names(paths):
    """(private names, mixin method names) defined by classes, or privately at module level, in these files."""
    private, mixin_methods = set(), set()
    for path in paths:
        for node in parse(path).body:  # module-level private functions and names count too
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                    and node.name.startswith("_") and not node.name.startswith("__"):
                private.add(node.name)
        for node in ast.walk(parse(path)):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                names = []
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names = [item.name]
                elif isinstance(item, ast.Assign):
                    names = [target.id for target in item.targets if isinstance(target, ast.Name)]
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    names = [item.target.id]
                for name in names:
                    if name.startswith("_") and not name.startswith("__"):
                        private.add(name)
                    elif node.name.endswith("Mixin") and not name.startswith("_") and not name.isupper():
                        mixin_methods.add(name)
    return private, mixin_methods


class PackageWallTests(unittest.TestCase):
    def test_outside_code_imports_only_the_api(self):
        for package in walled_packages():
            prefix = "sim.%s." % package
            allowed = {"sim.%s" % package, "sim.%s.api" % package}
            for path in outside_files(package):
                for module in imported_modules(path, parse(path)):
                    if module.startswith(prefix) and not any(module == a or module.startswith(a + ".")
                                                             for a in allowed - {"sim.%s" % package}):
                        self.fail("%s imports %s; use sim.%s.api" % (os.path.relpath(path, ROOT), module, package))

    def test_two_way_packages_never_reach_into_the_engine(self):
        """A package whose api.py says `WALL = "two-way"` imports nothing from sim.engine or sim.ui
        (UI excepted: it may import sim.engine.ui_port), only other packages' api, and puts no class
        into Sim's bases: the engine hands it what it needs through an adapter of its own."""
        sim_bases = sim_base_modules()
        for package in walled_packages():
            if wall_kind(package) != "two-way":
                continue
            allowed = {"sim.engine.ui_port"} if package == "ui" else set()
            others = [name for name in walled_packages() if name != package] + ["economy"]
            for path in python_files(os.path.join(SIM_DIR, package)):
                for module in imported_modules(path, parse(path)):
                    where = os.path.relpath(path, ROOT)
                    if any(module == root or module.startswith(root + ".") for root in ("sim.engine", "sim.ui")) \
                            and not module.startswith("sim.%s" % package) \
                            and not any(module == ok or module.startswith(ok + ".") for ok in allowed):
                        self.fail("%s imports %s; ask the engine through this package's adapter" % (where, module))
                    for other in others:
                        if module.startswith("sim.%s." % other) and not module.startswith("sim.%s.api" % other) \
                                and other != "economy":
                            self.fail("%s imports %s; use sim.%s.api" % (where, module, other))
            self.assertFalse([module for module in sim_bases if module.startswith("sim.%s" % package)],
                             "Sim inherits from sim/%s/" % package)

    def test_packages_split_from_the_engine_reach_the_economy_only_through_its_port(self):
        """test_economy_imports.py lets only sim/engine/economy_port*.py import sim.economy, but it
        scans sim/engine/ alone; these packages were part of it."""
        for directory in engine_side_dirs():
            if os.path.basename(directory) == "engine":
                continue
            for path in python_files(directory):
                for module in imported_modules(path, parse(path)):
                    self.assertFalse(module == "sim.economy" or module.startswith("sim.economy."),
                                     "%s imports %s" % (os.path.relpath(path, ROOT), module))

    def test_outside_code_reads_no_private_name_of_a_package(self):
        packages = list(walled_packages())
        every_file = list(python_files(SIM_DIR))
        for package in packages:
            package_dir = os.path.join(SIM_DIR, package) + os.sep
            inside = [path for path in every_file if path.startswith(package_dir)]
            elsewhere = [path for path in every_file if not path.startswith(package_dir)]
            private, _ = defined_names(inside)
            private -= defined_names(elsewhere)[0]
            for path in outside_files(package):
                for node in ast.walk(parse(path)):
                    if isinstance(node, ast.Attribute) and node.attr in private:
                        self.fail("%s:%d reads %s, private to sim/%s/" % (
                            os.path.relpath(path, ROOT), node.lineno, node.attr, package))

    def test_mixin_methods_are_called_through_the_port(self):
        every_file = list(python_files(SIM_DIR))
        for package in walled_packages():
            package_dir = os.path.join(SIM_DIR, package) + os.sep
            inside = [path for path in every_file if path.startswith(package_dir)]
            elsewhere = [path for path in every_file if not path.startswith(package_dir)]
            _, methods = defined_names(inside)
            methods.discard(package)
            methods -= set().union(*(defined_names([path])[1] | self._sim_defs(path) for path in elsewhere))
            for path in outside_files(package):
                for node, on_sim in sim_attributes(parse(path)):
                    if on_sim and node.attr in methods:
                        self.fail("%s:%d calls %s off Sim; use .%s.%s" % (
                            os.path.relpath(path, ROOT), node.lineno, node.attr, package, node.attr))

    @staticmethod
    def _sim_defs(path):
        """Names `class Sim` defines itself, so a name it overrides is not flagged."""
        names = set()
        for node in ast.walk(parse(path)):
            if isinstance(node, ast.ClassDef) and node.name == "Sim":
                names.update(item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))
        return names


SIM_NAMES = {"sim", "_sim"}


def sim_attributes(tree):
    """Every attribute access, with whether its receiver is the Sim: `sim.x`, `self._sim.x`,
    `self.sim.x`, or `self.x` inside `class Sim` or a `*Mixin` class (which `Sim` inherits)."""
    def visit(node, in_sim_class):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, child.name == "Sim" or child.name.endswith("Mixin"))
                continue
            if isinstance(child, ast.Attribute):
                receiver = child.value
                on_sim = ((isinstance(receiver, ast.Name) and (receiver.id in SIM_NAMES
                                                               or (receiver.id == "self" and in_sim_class)))
                          or (isinstance(receiver, ast.Attribute) and receiver.attr in SIM_NAMES))
                yield child, on_sim
            yield from visit(child, in_sim_class)
    yield from visit(tree, False)


if __name__ == "__main__":
    unittest.main()
