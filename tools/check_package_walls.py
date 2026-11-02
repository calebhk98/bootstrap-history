"""Find imports of a walled package's submodules from outside that package.

The walled packages are the libraries named in docs/architecture/PACKAGE_WALLS.md. Code outside a package (tests
aside) may import only its `api` module. The files are parsed with `ast`, never imported.
Prints `file:line: imports sim.<package>.<module>` for each violation and exits 1 when there is any.
"""
import ast
import os
import sys

WALLED_PACKAGES = ("economy", "agents", "labour", "geography", "ui")
DOOR_MODULE = "api"
REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIRECTORY = "sim/tests"


def imported_names(tree):
    """(line, dotted module name) for each name the tree imports from the `sim` package."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module == "sim" or node.module.startswith("sim."):
                for alias in node.names:
                    found.append((node.lineno, node.module + "." + alias.name))
    return found


def submodule_import(dotted_name):
    """The `sim.<package>.<module>` a dotted name reaches when it is a walled package's non-door module, else None."""
    parts = dotted_name.split(".")
    if len(parts) < 3 or parts[0] != "sim" or parts[1] not in WALLED_PACKAGES:
        return None
    if parts[2] == DOOR_MODULE:
        return None
    return ".".join(parts[:3])


def relative_path(path):
    return os.path.relpath(path, REPOSITORY_ROOT).replace(os.sep, "/")


def python_files():
    for directory, subdirectories, files in os.walk(REPOSITORY_ROOT):
        subdirectories[:] = sorted(name for name in subdirectories if not name.startswith(".") and name != "__pycache__")
        for file_name in sorted(files):
            if file_name.endswith(".py"):
                yield os.path.join(directory, file_name)


def owning_package(rel):
    """The walled package a repository-relative path lies inside, or None."""
    parts = rel.split("/")
    if len(parts) > 2 and parts[0] == "sim" and parts[1] in WALLED_PACKAGES:
        return parts[1]
    return None


def violations():
    found = set()
    for path in python_files():
        rel = relative_path(path)
        if rel == TESTS_DIRECTORY or rel.startswith(TESTS_DIRECTORY + "/"):
            continue
        with open(path, encoding="utf-8") as source:
            tree = ast.parse(source.read(), filename=rel)
        for line, dotted_name in imported_names(tree):
            module = submodule_import(dotted_name)
            if module is None or owning_package(rel) == module.split(".")[1]:
                continue
            found.add((rel, line, module))
    return sorted(found)


def main():
    found = violations()
    for rel, line, module in found:
        print(f"{rel}:{line}: imports {module}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
