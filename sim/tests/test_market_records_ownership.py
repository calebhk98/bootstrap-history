"""Complaint 359: only the market writes the market's records.

The year's flows, the commodity book and the foreign book are written by the market modules
alone. A seller or buyer (the founder, a firm, the state, a trader) asks `Sim.goods_market` and
never reaches into the records. The scan finds writes made straight through the record's name;
a record copied into a local first is not seen, so the modules that hold records stay few.
"""
import ast
import os

from .harness import *  # noqa: F401,F403

RECORDS = {"market_flows", "market_book", "foreign_market_book", "market_offers"}
MUTATORS = {"setdefault", "update", "pop", "clear", "append", "extend", "remove", "popitem", "__setitem__"}
MARKET_MODULES = {
    "state.py",              # declares them
    "market_clearing.py",    # the clearing of the home book
    "goods_market_api.py",   # the one door sellers and buyers use
    "foreign_economies.py",  # the partners' books and the trade between them and the home book
}
SCANNED = (os.path.join("sim", "engine"), os.path.join("sim", "world"))


def _record_root(node):
    """The record an expression is rooted in (`x.market_flows["a"]["b"]` is rooted in market_flows)."""
    while isinstance(node, (ast.Subscript, ast.Attribute, ast.Call)):
        if isinstance(node, ast.Attribute) and node.attr in RECORDS:
            return node.attr
        node = node.func if isinstance(node, ast.Call) else node.value
    return None


class _WriteFinder(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.writes = []

    def _target(self, target, lineno):
        record = _record_root(target)
        if record:
            self.writes.append((self.filename, lineno, record))

    def visit_Assign(self, node):
        for target in node.targets:
            self._target(target, node.lineno)
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        self._target(node.target, node.lineno)
        self.generic_visit(node)

    def visit_Delete(self, node):
        for target in node.targets:
            self._target(target, node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr in MUTATORS:
            record = _record_root(node.func.value)
            if record:
                self.writes.append((self.filename, node.lineno, record))
        self.generic_visit(node)


def writes_in(source, filename="synthetic.py"):
    finder = _WriteFinder(filename)
    finder.visit(ast.parse(source))
    return finder.writes


def outside_the_market():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    found = []
    for scanned in SCANNED:
        for folder, _dirs, files in os.walk(os.path.join(root, scanned)):
            for name in sorted(files):
                if name.endswith(".py") and name not in MARKET_MODULES:
                    path = os.path.join(folder, name)
                    with open(path, encoding="utf-8") as handle:
                        found.extend(writes_in(handle.read(), os.path.relpath(path, root)))
    return found


violations = outside_the_market()
check("no module outside the market writes a market record", not violations, violations[:6])

check("the scan sees an assignment into the year's flows",
      writes_in("def f(self):\n    self.state.economy.market_flows['sold']['iron'] = 1\n"))
check("...an augmented assignment into the book",
      writes_in("def f(economy):\n    economy.market_book['iron']['stock_tonnes'] += 1\n"))
check("...a mutating call on a record",
      writes_in("def f(economy):\n    economy.foreign_market_book.setdefault('han', {})\n"))
check("...and a plain read is not a write",
      not writes_in("def f(economy):\n    return economy.market_book['iron']['stock_tonnes']\n"))
