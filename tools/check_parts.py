"""Static check of the module/part structure. Run from the repository root; prints one line per problem, exits 1 if any.

1. Every view, command, phase and provision name a module_spec.py declares resolves on the module's implementation: a method of
   the class, or a method of exactly one class in its PARTS.
2. Every `self.parts.<part>.<member>` in a part names a part of the same module and a member that part's class has.
3. Every other `self.<name>` in a part is defined on the part (method, class attribute, assigned anywhere in the class or its
   bases) or is one of Part's own names.
4. A module class derives from Module only.
5. No code under `sim/` (tests excluded) reaches a private member of a part: `...parts.<name>._member`, or `_member` on a local
   or `self` attribute that was assigned from `...parts.<name>`. A part's privates are for the part's own class."""
import ast
import glob
import importlib
import inspect
import os
import sys
import textwrap

sys.path.insert(0, os.getcwd())
from sim.assembly.api import Module, Part  # noqa: E402
from sim.assembly.spec import declared_methods  # noqa: E402

PART_NAMES = set(dir(Part)) | {"module", "parts", "needs", "clock", "module_id", "kernels"}


def attributes_of(cls):
	"""Names a class and its bases define: methods, class attributes and anything assigned to self."""
	names = set()
	for klass in cls.__mro__:
		if klass is object:
			continue
		try:
			tree = ast.parse(textwrap.dedent(inspect.getsource(klass)))
		except (OSError, TypeError):
			continue
		for node in ast.walk(tree):
			if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and isinstance(node.value, ast.Name) \
					and node.value.id == "self":
				names.add(node.attr)
		names |= set(vars(klass))
	return names


def is_parts_member(node):
	"""True for `<anything>.parts.<name>` and a bare `parts.<name>`."""
	if not isinstance(node, ast.Attribute):
		return False
	owner = node.value
	return (isinstance(owner, ast.Attribute) and owner.attr == "parts") or (isinstance(owner, ast.Name) and owner.id == "parts")


def is_private(name):
	return name.startswith("_") and not name.startswith("__")


def part_aliases(scope):
	"""Names (`x`, or `self.x`) assigned from `...parts.<name>` inside one scope."""
	aliases = set()
	for node in ast.walk(scope):
		if isinstance(node, ast.Assign) and is_parts_member(node.value):
			for target in node.targets:
				if isinstance(target, ast.Name):
					aliases.add(target.id)
				elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
					aliases.add("self." + target.attr)
	return aliases


def private_reaches(path):
	"""(line, text) for each private member reached on a part in one file."""
	with open(path, encoding="utf-8") as handle:
		tree = ast.parse(handle.read(), path)
	found = set()
	for scope in ast.walk(tree):
		if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
			continue
		aliases = part_aliases(scope)
		for node in ast.walk(scope):
			if not (isinstance(node, ast.Attribute) and is_private(node.attr)):
				continue
			owner = node.value
			if is_parts_member(owner):
				found.add((node.lineno, "%s.%s" % (ast.unparse(owner), node.attr)))
			elif isinstance(owner, ast.Name) and owner.id in aliases:
				found.add((node.lineno, "%s.%s (a part)" % (owner.id, node.attr)))
			elif isinstance(owner, ast.Attribute) and isinstance(owner.value, ast.Name) and owner.value.id == "self" \
					and "self." + owner.attr in aliases:
				found.add((node.lineno, "self.%s.%s (a part)" % (owner.attr, node.attr)))
	return sorted(found)


def check_private_reaches(problems):
	for path in sorted(glob.glob("sim/**/*.py", recursive=True)):
		if path.startswith("sim/tests/"):
			continue
		for line, text in private_reaches(path):
			problems.append("%s:%d: reaches a private member of a part: %s" % (path, line, text))


def check_module(pkg, problems):
	spec_file = "sim/%s/module_spec.py" % pkg
	if not os.path.exists(spec_file):
		return
	module = importlib.import_module("sim.%s.module_spec" % pkg)
	for spec in getattr(module, "MODULE_SPECS", ()):
		implementation = spec.implementation
		if implementation.__bases__ != (Module,) and implementation is not Module:
			problems.append("%s: %s derives from %s, not Module alone" % (pkg, implementation.__name__,
			                                                             [base.__name__ for base in implementation.__bases__]))
		for name in declared_methods(spec):
			if callable(getattr(implementation, name, None)):
				continue
			holders = [part for part, cls in implementation.PARTS.items() if callable(getattr(cls, name, None))]
			if len(holders) != 1:
				problems.append("%s: declared %s resolves on %s" % (pkg, name, holders or "nothing"))
		parts = implementation.PARTS
		for part_name, part_class in parts.items():
			if not issubclass(part_class, Part):
				problems.append("%s: part %s is not a Part" % (pkg, part_name))
				continue
			own = attributes_of(part_class)
			tree = ast.parse(textwrap.dedent(inspect.getsource(part_class)))
			for node in ast.walk(tree):
				if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self" \
						and node.attr not in own and node.attr not in PART_NAMES:
					problems.append("%s.%s: self.%s is not defined (line %d)" % (pkg, part_class.__name__, node.attr, node.lineno))
				if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) \
						and isinstance(node.value.value, ast.Attribute) and node.value.value.attr == "parts" \
						and isinstance(node.value.value.value, ast.Name) and node.value.value.value.id == "self":
					target, member = node.value.attr, node.attr
					if target not in parts:
						problems.append("%s.%s: self.parts.%s is not a part (line %d)" % (pkg, part_class.__name__, target, node.lineno))
					elif member not in attributes_of(parts[target]):
						problems.append("%s.%s: self.parts.%s.%s is not defined (line %d)" % (
							pkg, part_class.__name__, target, member, node.lineno))


def main(names):
	problems = []
	packages = names or sorted(os.path.basename(os.path.dirname(path)) for path in glob.glob("sim/*/module_spec.py"))
	for pkg in packages:
		try:
			check_module(pkg, problems)
		except Exception as error:  # an import failure is a finding
			problems.append("%s: %s: %s" % (pkg, type(error).__name__, error))
	if not names:
		check_private_reaches(problems)
	for line in problems:
		print(line)
	return 1 if problems else 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
