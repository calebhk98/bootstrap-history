"""Fail when a module writes a part of the economy record that it does not own.

Each owned part of `EconomyRecord` (and `memory`, `state_budget`, and the agent tables) names, in an `OWNERS` tuple, the
`sim/economy` modules allowed to WRITE it: assign a field, item-assign, call a mutating method on a store, or put an
element back into a table. Reads may cross domains. `sim/markets` owns none and goes through `sim/economy/api.py`.

The files are parsed with `ast`, never run. A write is found through `record.<part>...`, `<x>.record.<part>...`, through
a local alias of one (`land = record.land`, `rows = record.land.tenancies[tile]`, `for key, row in part.store.items()`)
and through a parameter annotated with a part's class. A write that goes through a method of the part itself is the
owner's own code and is not flagged. Prints `file:line: <module> writes <part>` and exits 1 when there is any.
`--all` lists every write found, owned or not.
"""
import ast
import os
import sys

REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPOSITORY_ROOT)

from sim.economy.api import EconomyRecord  # noqa: E402

SCANNED = ("sim/economy", "sim/markets")
MUTATING_METHODS = frozenset((
    "append", "extend", "insert", "remove", "pop", "popitem", "clear", "update", "setdefault", "add", "discard",
    "sort", "reverse", "difference_update", "intersection_update", "symmetric_difference_update"))
READING_METHODS = frozenset(("get", "items", "values", "keys", "copy"))
PASSING_FUNCTIONS = frozenset(("sorted", "list", "tuple", "reversed", "iter", "enumerate"))


def record_owners():
    """{part name: (owners, class name)} for every part and table the record declares."""
    owners = {}
    for name, owner_modules in EconomyRecord.owners_by_part().items():
        owners[name] = tuple(owner_modules)
    return owners


def part_classes():
    """{class name: part name}: the classes whose instances are a whole part or a row of a table."""
    return EconomyRecord.part_class_names()


def is_record(node):
    """True for `record`, `self.record`, `economy.record`."""
    return (isinstance(node, ast.Name) and node.id == "record") or (isinstance(node, ast.Attribute) and node.attr == "record")


class Finder(ast.NodeVisitor):
    def __init__(self, module, parts, classes):
        self.module = module
        self.parts = parts
        self.classes = classes
        self.scopes = [{}]
        self.writes = []

    def part_of(self, node):
        """The part a pure attribute/subscript chain reaches (through `record`, an alias or an annotated name), else None."""
        while True:
            if isinstance(node, ast.Subscript):
                node = node.value
            elif isinstance(node, ast.Attribute):
                if is_record(node.value) and node.attr in self.parts:
                    return node.attr
                node = node.value
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in READING_METHODS:
                node = node.func.value
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in PASSING_FUNCTIONS and node.args:
                node = node.args[0]
            elif isinstance(node, ast.Name):
                return self.scopes[-1].get(node.id)
            else:
                return None

    def note(self, part, node):
        self.writes.append((node.lineno, part))

    def function(self, node):
        scope = dict(self.scopes[-1])
        arguments = node.args
        for argument in arguments.posonlyargs + arguments.args + arguments.kwonlyargs:
            annotation = argument.annotation
            name = None
            if isinstance(annotation, ast.Name):
                name = annotation.id
            elif isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
                name = annotation.value
            if name in self.classes:
                scope[argument.arg] = self.classes[name]
            else:
                scope.pop(argument.arg, None)
        self.scopes.append(scope)
        self.generic_visit(node)
        self.scopes.pop()

    visit_FunctionDef = function
    visit_AsyncFunctionDef = function

    def target(self, target):
        """A store to `target`: a write when it reaches into a part below a name."""
        if isinstance(target, (ast.Tuple, ast.List)):
            for each in target.elts:
                self.target(each)
        elif isinstance(target, (ast.Attribute, ast.Subscript)):
            part = self.part_of(target)
            if part is not None:
                self.note(part, target)

    def bind(self, target, value):
        """`name = <chain into a part>` makes `name` an alias; any other binding of `name` ends one."""
        if isinstance(target, (ast.Tuple, ast.List)):
            for each in target.elts:
                self.bind(each, None)
        elif isinstance(target, ast.Name):
            part = self.part_of(value) if value is not None else None
            if part is not None and not (isinstance(value, ast.Name) and value.id == target.id):
                self.scopes[-1][target.id] = part
            else:
                self.scopes[-1].pop(target.id, None)

    def visit_Assign(self, node):
        self.visit(node.value)
        for target in node.targets:
            self.target(target)
            self.bind(target, node.value)

    def visit_AnnAssign(self, node):
        if node.value is not None:
            self.visit(node.value)
            self.target(node.target)
            self.bind(node.target, node.value)

    def visit_AugAssign(self, node):
        self.visit(node.value)
        self.target(node.target)

    def visit_Delete(self, node):
        for target in node.targets:
            self.target(target)

    def visit_For(self, node):
        self.visit(node.iter)
        part = self.part_of(node.iter)
        names = [each.id for each in ast.walk(node.target) if isinstance(each, ast.Name)]
        for name in names:
            if part is not None:
                self.scopes[-1][name] = part
            else:
                self.scopes[-1].pop(name, None)
        for statement in node.body + node.orelse:
            self.visit(statement)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr in MUTATING_METHODS:
            part = self.part_of(node.func.value)
            if part is not None:
                self.note(part, node)
        self.generic_visit(node)


def modules_to_scan():
    for directory in SCANNED:
        for name in sorted(os.listdir(os.path.join(REPOSITORY_ROOT, directory))):
            if name.endswith(".py"):
                yield directory, name


def findings():
    owners = record_owners()
    classes = part_classes()
    found = []
    for directory, name in modules_to_scan():
        path = os.path.join(directory, name)
        with open(os.path.join(REPOSITORY_ROOT, path), encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), path)
        finder = Finder(name[:-3], owners, classes)
        finder.visit(tree)
        in_economy = directory == "sim/economy"
        for line, part in finder.writes:
            allowed = in_economy and finder.module in owners[part]
            found.append((path, line, finder.module, part, allowed))
    return found


def main():
    show_all = "--all" in sys.argv
    failures = 0
    for path, line, module, part, allowed in findings():
        if allowed and not show_all:
            continue
        failures += 0 if allowed else 1
        print("%s:%d: %s writes %s%s" % (path, line, module, part, "" if allowed else " (not an owner)"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
