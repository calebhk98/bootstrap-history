"""Complaint 508: only the agent economy writes its markets' records.

What each market sold, left unsold and left unmet, and the curves and runs of years it keeps, are fields of
`economy.record` (sim/economy/record.py). Code outside `sim/economy/` reads them through `sim.economy.api`
(`market_record`, `traded_volumes`) and never assigns into them. The scan finds writes made straight through the
record's name; a record copied into a local first is not seen.
"""
QUICK_TOPIC = True

import ast
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OWNER = os.path.join("sim", "economy")
MARKET_FIELDS = {"volumes", "unsold", "unmet", "curves", "margin_years"}
MUTATORS = {"setdefault", "update", "pop", "clear", "append", "extend", "remove", "popitem", "__setitem__"}


def market_field_of(node):
    """The market field an expression is rooted in when it hangs off a `.record`, else None."""
    while isinstance(node, (ast.Subscript, ast.Attribute, ast.Call)):
        if isinstance(node, ast.Attribute) and node.attr in MARKET_FIELDS \
                and isinstance(node.value, ast.Attribute) and node.value.attr == "record":
            return node.attr
        node = node.func if isinstance(node, ast.Call) else node.value
    return None


class WriteFinder(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.writes = []

    def note(self, target, lineno):
        field_name = market_field_of(target)
        if field_name:
            self.writes.append((self.filename, lineno, field_name))

    def visit_Assign(self, node):
        for target in node.targets:
            self.note(target, node.lineno)
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        self.note(node.target, node.lineno)
        self.generic_visit(node)

    def visit_Delete(self, node):
        for target in node.targets:
            self.note(target, node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr in MUTATORS:
            self.note(node.func.value, node.lineno)
        self.generic_visit(node)


def writes_in(source, filename="synthetic.py"):
    finder = WriteFinder(filename)
    finder.visit(ast.parse(source))
    return finder.writes


def writes_outside_the_economy():
    found = []
    for folder, _dirs, files in os.walk(os.path.join(ROOT, "sim")):
        relative = os.path.relpath(folder, ROOT)
        if relative == OWNER or relative.startswith(OWNER + os.sep) or relative.startswith(os.path.join("sim", "tests")):
            continue
        for name in sorted(files):
            if name.endswith(".py"):
                path = os.path.join(folder, name)
                with open(path, encoding="utf-8") as handle:
                    found.extend(writes_in(handle.read(), os.path.relpath(path, ROOT)))
    return found


class EconomyMarketRecordWallTests(unittest.TestCase):
    def test_nothing_outside_the_economy_writes_a_market_record(self):
        self.assertEqual(writes_outside_the_economy(), [])

    def test_the_scan_sees_an_assignment_into_the_record(self):
        self.assertTrue(writes_in("def f(economy):\n    economy.record.volumes['a|b'] = 1.0\n"))

    def test_the_scan_sees_an_augmented_assignment(self):
        self.assertTrue(writes_in("def f(economy):\n    economy.record.unsold['a|b'] += 1.0\n"))

    def test_the_scan_sees_a_mutating_call(self):
        self.assertTrue(writes_in("def f(sim):\n    sim.economy.record.unmet.update({})\n"))

    def test_a_plain_read_is_not_a_write(self):
        self.assertFalse(writes_in("def f(economy):\n    return economy.record.volumes.get('a|b', 0.0)\n"))

    def test_a_field_of_another_record_is_not_a_market_record(self):
        self.assertFalse(writes_in("def f(church):\n    church.record.need['volumes'] = 1.0\n"))


if __name__ == "__main__":
    unittest.main()
