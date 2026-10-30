"""Every `from X import` in sim/ and mods/ names a module that exists, including imports inside functions that only a
game reaches. Run after every merge: a moved module can leave a lazy import that the quick tier never executes.
Run from the repository root; prints the broken imports, one per line, and exits non-zero when there are any."""
import ast
import glob
import importlib.util
import sys

sys.path.insert(0, ".")
broken = []
for path in sorted(glob.glob("sim/**/*.py", recursive=True) + glob.glob("mods/**/*.py", recursive=True)):
    package = path[:-3].split("/")[:-1]
    for node in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            base = package[:len(package) - (node.level - 1)] if node.level > 1 else package
            module = ".".join(base + ([node.module] if node.module else []))
        elif node.module and node.module.startswith("sim."):
            module = node.module
        else:
            continue
        try:
            found = importlib.util.find_spec(module)
        except ModuleNotFoundError:
            found = None
        if found is None:
            broken.append("%s:%d imports %s, which does not exist" % (path, node.lineno, module))
print("\n".join(broken))
sys.exit(1 if broken else 0)
