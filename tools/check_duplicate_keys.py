"""Print every dict literal in sim/ and mods/ that names one key twice: Python keeps the last silently, which is how a
module spec's reads lost a view. Prints nothing when clean."""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def duplicate_keys(path):
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            seen = set()
            for key in node.keys:
                if isinstance(key, ast.Constant):
                    if key.value in seen:
                        yield key.lineno, key.value
                    seen.add(key.value)


def main():
    found = 0
    for top in ("sim", "mods"):
        for directory, _subdirectories, files in os.walk(os.path.join(ROOT, top)):
            for name in sorted(files):
                if name.endswith(".py"):
                    path = os.path.join(directory, name)
                    for line, key in duplicate_keys(path):
                        print("%s:%d: key %r appears twice in one dict" % (os.path.relpath(path, ROOT), line, key))
                        found += 1
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
