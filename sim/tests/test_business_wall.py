"""Ratchet wall: only the business object and the plant kernel may compute a business's crew, upkeep or takings.

Stage 0 of docs/architecture/FIRMS_OWN_PLANTS_PLAN.md. Outside `sim/agents/business*.py` and `sim/world/plant_figures.py`
(which do not exist yet), no function may define or call a crew/upkeep/takings function from CREW_UPKEEP_TAKINGS_NAMES,
or read a node money field (NODE_MONEY_FIELDS) by constant key. Today's offenders are listed in
`business_wall_allowlist.txt` (sorted, one `path::function` per line). The list can only shrink: a new offender fails the
test; an entry that no longer offends is reported as a warning so it can be pruned.

The `art`/`sch` fields are not scanned: research and project-start code reads them for the same purpose as operating
code, and the AST cannot tell the two apart. They move with the plant kernel in stage 2.
"""

QUICK_TOPIC = True

import ast
import functools
import os
import unittest
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ALLOWLIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "business_wall_allowlist.txt")

CREW_UPKEEP_TAKINGS_NAMES = frozenset((
    "venture_hands", "venture_foreman", "institution_upkeep", "venture_real_upkeep", "venture_real_earnings",
    "concern_takings", "concern_wage_bill", "plant_crew", "venture_ramp", "concern_upkeep"))
NODE_MONEY_FIELDS = frozenset(("up", "rev", "up_hours", "rev_hours", "cap_hours"))
DICT_READ_METHODS = frozenset(("get", "setdefault", "pop"))
OWNER_PREFIXES = ("sim/agents/business",)
OWNER_FILES = ("sim/world/plant_figures.py",)


def is_owner_file(relative):
    return relative in OWNER_FILES or any(relative.startswith(prefix) for prefix in OWNER_PREFIXES)


def scanned_files():
    for folder, subfolders, filenames in os.walk(os.path.join(ROOT, "sim")):
        subfolders[:] = sorted(name for name in subfolders if name not in ("tests", "__pycache__"))
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                path = os.path.join(folder, filename)
                relative = os.path.relpath(path, ROOT).replace(os.sep, "/")
                if not is_owner_file(relative):
                    yield path, relative


def called_name(call):
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def constant_string(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def offences_in(tree):
    """Names of the functions ('<module>' at top level) that define or call a listed name or read a money field."""
    found = set()

    def visit(node, function_name):
        for child in ast.iter_child_nodes(node):
            inner = function_name
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                inner = child.name
                if child.name in CREW_UPKEEP_TAKINGS_NAMES:
                    found.add(child.name)
            elif isinstance(child, ast.Call):
                if called_name(child) in CREW_UPKEEP_TAKINGS_NAMES:
                    found.add(function_name)
                if (isinstance(child.func, ast.Attribute) and child.func.attr in DICT_READ_METHODS and child.args
                        and constant_string(child.args[0]) in NODE_MONEY_FIELDS):
                    found.add(function_name)
            elif isinstance(child, ast.Subscript) and constant_string(child.slice) in NODE_MONEY_FIELDS:
                found.add(function_name)
            visit(child, inner)

    visit(tree, "<module>")
    return found


@functools.lru_cache(maxsize=None)
def current_offenders():
    offenders = set()
    for path, relative in scanned_files():
        with open(path, encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
        offenders.update("%s::%s" % (relative, name) for name in offences_in(tree))
    return frozenset(offenders)


def allowlist():
    with open(ALLOWLIST_PATH, encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


class BusinessWallTests(unittest.TestCase):
    def test_allowlist_is_sorted_and_unique(self):
        entries = allowlist()
        self.assertEqual(entries, sorted(set(entries)))

    def test_no_new_code_computes_crew_upkeep_or_takings_outside_the_business(self):
        new = current_offenders() - set(allowlist())
        self.assertEqual(sorted(new), [], "new crew/upkeep/takings code outside the business object and plant kernel; "
                                          "route it through the business instead of adding to the allowlist")

    def test_stale_allowlist_entries_are_reported_for_pruning(self):
        stale = sorted(set(allowlist()) - current_offenders())
        if stale:
            warnings.warn("business wall allowlist entries no longer offend, delete them from %s:\n  %s"
                          % (os.path.basename(ALLOWLIST_PATH), "\n  ".join(stale)))

    def test_detector_sees_a_deliberate_offender(self):
        tree = ast.parse("def f(sim, node):\n    return sim.venture_hands(node) + node['up'] + node.get('rev_hours')\n"
                         "def g():\n    # venture_hands\n    return 'up'\n")
        self.assertEqual(offences_in(tree), {"f"})


if __name__ == "__main__":
    unittest.main()
