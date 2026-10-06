"""The source files a module can run: itself, its packages, and every sim module it imports,
directly or through others, at the top or inside a function. Found by reading the syntax
tree, so nothing is imported. Imports named by a runtime string are not seen."""
import ast
import os
from typing import Iterable, List, Optional


def _path_of(root: str, module: str) -> Optional[str]:
    base = os.path.join(root, *module.split("."))
    if os.path.isfile(base + ".py"):
        return base + ".py"
    package = os.path.join(base, "__init__.py")
    return package if os.path.isfile(package) else None


def _imported_names(path: str, package: str) -> List[str]:
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package.split(".")
                parts = parts[:len(parts) - (node.level - 1)]
                base = ".".join(parts + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            # `from package import name` may name a submodule; a name that is not one is skipped.
            names += [base] + [base + "." + alias.name for alias in node.names]
    return names


def source_files(root: str, modules: Iterable[str], top_package: str = "sim") -> List[str]:
    """Sorted paths of every file under `root` that `modules` can import within `top_package`."""
    found = {}
    pending = list(modules)
    while pending:
        module = pending.pop()
        if module in found or not (module == top_package or module.startswith(top_package + ".")):
            continue
        path = _path_of(root, module)
        found[module] = path
        if path is None:
            continue
        parts = module.split(".")
        pending += [".".join(parts[:count]) for count in range(1, len(parts))]
        package = module if path.endswith("__init__.py") else ".".join(parts[:-1])
        pending += _imported_names(path, package)
    return sorted(path for path in found.values() if path)
