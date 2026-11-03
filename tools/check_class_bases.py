"""Find classes that bundle behaviour by inheriting it, anywhere in `sim/` except `sim/tests`.

A class that is named `...Mixin`, or that has
more than one base, composes by inheritance; its behaviour belongs in plain parts it owns and callers address as
`<owner>.<part>.<method>`. The files are parsed with `ast`, never imported.

Allowed several bases (a base that is not a bundle of behaviour):
  - `Actor(Reviewable, Borrower)`: two interfaces of overridable defaults the actors' subclasses override.
  - a class whose extra bases are only `Protocol`, `Generic`, `Enum`, `NamedTuple`, `TypedDict` or exception families (names ending `Error` or `Exception`).
  - `CollectionView`.
Prints `file:line: class Name(bases)` for each violation and exits 1 when there is any. A class in `PENDING` is printed
with a `pending` prefix and does not fail the run.
"""
import ast
import os
import sys

PACKAGES = ("sim",)
EXCLUDED = ("sim/tests",)
REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_MULTIPLE = {("agents/base.py", "Actor"): {"Reviewable", "Borrower"}}
TYPING_BASES = {"Protocol", "Generic", "Enum", "IntEnum", "NamedTuple", "TypedDict", "Exception", "ValueError", "RuntimeError",
                "KeyError", "TypeError", "object", "ABC"}
ALLOWED_CLASSES = {"CollectionView"}
# Classes still composed by inheritance, waiting for their own split: reported on stdout after the violations, not failing.
PENDING = set()


def base_name(node):
    """The last dotted name of a base expression (`typing.Protocol` and `Protocol[T]` give `Protocol`)."""
    if isinstance(node, ast.Subscript):
        return base_name(node.value)
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ast.dump(node)


def violations_in(path, relative):
    """(line, description) for each class in the file that composes by inheritance."""
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), path)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name in ALLOWED_CLASSES:
            continue
        bases = [base_name(base) for base in node.bases]
        description = "class %s(%s)" % (node.name, ", ".join(bases))
        if node.name.endswith("Mixin"):
            found.append((node.lineno, description + " is a mixin"))
            continue
        extra = [name for name in bases if name not in TYPING_BASES and not name.endswith(('Error', 'Exception'))]
        if len(extra) <= 1:
            continue
        allowed = None
        for (suffix, name), names in ALLOWED_MULTIPLE.items():
            if node.name == name and relative.endswith(suffix):
                allowed = names
        if allowed is not None and set(extra) <= allowed:
            continue
        found.append((node.lineno, description + " has more than one behaviour base"))
    return found


def main():
    count = 0
    for package in PACKAGES:
        for directory, names, files in os.walk(os.path.join(REPOSITORY_ROOT, package)):
            names[:] = sorted(name for name in names if os.path.relpath(os.path.join(directory, name), REPOSITORY_ROOT) not in EXCLUDED)
            for name in sorted(files):
                if not name.endswith(".py"):
                    continue
                path = os.path.join(directory, name)
                relative = os.path.relpath(path, REPOSITORY_ROOT)
                for line, description in violations_in(path, relative):
                    pending = any(description.startswith("class %s(" % name) for name in PENDING)
                    print("%s%s:%d: %s" % ("pending " if pending else "", relative, line, description))
                    count += 0 if pending else 1
    return 1 if count else 0


if __name__ == "__main__":
    sys.exit(main())
