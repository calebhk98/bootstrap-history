"""Class names that mean two different classes where a reader (or an import) can mix them up.

A name is reported when
1. two classes of that name are defined in the same package of sim/ (the package is the first directory under sim/, so
   sim/labour/wages.py and sim/labour/market/records.py are one package), or
2. a module imports the name from another package while a module of its own package defines a different class of that name.
Same-named Part and Protocol classes in different packages are not reported. Tests are excluded.

Run from the repository root; prints one line per problem and exits 1 if any."""
import ast
import collections
import sys

sys.path.insert(0, "tools")
from class_index import Index  # noqa: E402

# Pairs the owner accepts: (class name, path of one definition, path of the other). Each entry needs a comment saying why.
ALLOWED = set()


def package_of(path):
    parts = path.split("/")
    return parts[1] if parts[0] == "sim" and len(parts) > 2 else "sim"


def main():
    index = Index()
    definitions = collections.defaultdict(list)       # class name -> [(path, line, module name)]
    for module in index.modules.values():
        if not module.path.startswith("sim/"):
            continue
        for name, nodes in module.classes.items():
            for node in nodes:
                definitions[name].append((module.path, node.lineno, module.name))
    problems = []
    for name, places in sorted(definitions.items()):
        by_package = collections.defaultdict(list)
        for place in places:
            by_package[package_of(place[0])].append(place)
        for package, same in sorted(by_package.items()):
            if len(same) > 1:
                paths = sorted(same)
                if all((name, a[0], b[0]) in ALLOWED for a in paths for b in paths if a < b):
                    continue
                problems.append("class %s is defined %d times in sim/%s: %s" % (name, len(same), package, ", ".join("%s:%d" % p[:2] for p in paths)))
        # an import of the name that resolves to a different class than one defined elsewhere in the importer's package
        seen = set()
        for module in index.modules.values():
            if not module.path.startswith("sim/") or name not in module.imports or name in module.classes:
                continue
            found = index.follow(module.name, name)
            if found is None or found[0] != "class":
                continue
            target = (found[1], found[2].lineno)
            other = index.modules[found[1]].path
            if package_of(other) == package_of(module.path):
                continue                                  # two definitions in one package are reported above
            for path, line, defining in definitions[name]:
                if package_of(path) == package_of(module.path) and (defining, line) != target and defining != module.name:
                    if (name, *sorted([path, other])) in ALLOWED or (module.path, name) in seen:
                        continue
                    seen.add((module.path, name))
                    problems.append("%s imports %s from %s, but %s:%d also defines a class %s" % (module.path, name, other, path, line, name))
    if problems:
        print("\n".join(problems))
    sys.exit(1 if problems else 0)


main()
