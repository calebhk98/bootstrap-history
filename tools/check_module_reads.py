"""Every view a module reads through `needs.<name>` is declared in its spec, so the assembled module can answer it. A test host
hands a module any view it is given, so an undeclared read passes the unit tests and fails only in a built game. Prints each
undeclared read as module, view and the first place it is read, and exits non-zero when there are any. Run from the repository
root after a module move."""
import glob
import os
import re
import sys

sys.path.insert(0, ".")
from sim.engine import game_assembly  # noqa: E402

READ = re.compile(r"\bneeds\.([a-z_][a-z0-9_]*)")


def undeclared_reads(specs):
    """[(module id, view name, first place)] of the published views a module's package reads without declaring them."""
    published = {view.name for spec in specs.values() for view in spec.publishes}
    published |= {point.name for spec in specs.values() for point in spec.extension_points}
    found = []
    for module_id, spec in sorted(specs.items()):
        package = os.path.join("sim", module_id)
        if not os.path.isdir(package):
            continue
        declared = set(spec.reads) | set(spec.optional_reads) | {view.name for view in spec.publishes}
        declared |= {point.name for point in spec.extension_points}
        first_place = {}
        for path in sorted(glob.glob(package + "/**/*.py", recursive=True)):
            for number, line in enumerate(open(path, encoding="utf-8"), 1):
                for name in READ.findall(line):
                    if name in published and name not in declared:
                        first_place.setdefault(name, "%s:%d" % (path, number))
        found.extend((module_id, name, place) for name, place in sorted(first_place.items()))
    return found


if __name__ == "__main__":
    missing = undeclared_reads(game_assembly.build(None, False).applied.specs)
    for module_id, name, place in missing:
        print("%s reads %s undeclared (%s)" % (module_id, name, place))
    sys.exit(1 if missing else 0)
