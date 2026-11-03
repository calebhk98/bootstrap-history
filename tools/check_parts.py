"""Static check of the module/part structure. Run from the repository root; prints one line per problem, exits 1 if any.

1. Every view, command, phase and provision name a module_spec.py declares resolves on the module's implementation: a method of
   the class, or a method of exactly one class in its PARTS.
2. Every `self.parts.<part>` in a part (with or without a member after it) names a part of the same module, and every `self.parts.<part>.<member>` names a part of the same module and a member that part's class has; when the member
   is assigned in the part's methods from a constructor call that resolves, `.<submember>` is checked against that class too.
3. Every other `self.<name>` in a part is defined on the part (method, class attribute, assigned anywhere in the class or its
   bases) or is one of Part's own names.
4. A module class derives from Module only.
5. No code under `sim/` (tests excluded) reaches a private member of a part: `...parts.<name>._member` (the owner is any name ending in `parts`, so
   `_parts` too), or `_member` on a local or `self` attribute that was assigned from `...parts.<name>`. A part's privates are for the part's own class.
6. Every `self.world.<name>` and `self.seat.<name>` in a part (and on a local alias of either) is a member of the world_state or seat_state
   class its module spec declares; a spec that declares none for that slot is skipped.
7. Every `parts.<name>.<member>` (also on `economy.parts` and `port.parts`) in sim/markets names a member of the class AgentParts
   (sim/markets/port_parts.py, a plain holder) builds that attribute from."""
import ast
import dataclasses
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


def member_classes(part_class):
	"""{attribute: class} for each `self.<attribute> = Class(...)` in the part's methods whose class resolves in the part's module
	and answers every attribute (no `__getattr__`)."""
	module = sys.modules.get(part_class.__module__)
	found = {}
	try:
		tree = ast.parse(textwrap.dedent(inspect.getsource(part_class)))
	except (OSError, TypeError):
		return found
	for function in ast.walk(tree):
		if not isinstance(function, ast.FunctionDef):
			continue
		for node in ast.walk(function):
			if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)):
				continue
			klass = getattr(module, node.value.func.id, None)
			if not inspect.isclass(klass) or hasattr(klass, "__getattr__"):
				continue
			for target in node.targets:
				if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
					found[target.attr] = klass
	return found


def is_parts_member(node):
	"""True for `<anything>.<owner>.<name>` and a bare `<owner>.<name>`, where the owner's name ends in `parts` (`parts`, `_parts`)."""
	if not isinstance(node, ast.Attribute):
		return False
	owner = node.value
	return (isinstance(owner, ast.Attribute) and owner.attr.endswith("parts")) or (isinstance(owner, ast.Name) and owner.id.endswith("parts"))


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


def state_attributes(state_class):
	"""Names a state class answers to: dir(), dataclass fields and anything its methods assign to self."""
	names = set(dir(state_class))
	if dataclasses.is_dataclass(state_class):
		names |= {field.name for field in dataclasses.fields(state_class)}
	return names | attributes_of(state_class)


def state_reaches(part_class, slot_attributes):
	"""(line, slot, name) for each `self.world.X` / `self.seat.X` (or a local alias of either) in a part whose X the slot's state class lacks."""
	tree = ast.parse(textwrap.dedent(inspect.getsource(part_class)))
	first_line = inspect.getsourcelines(part_class)[1] - 1
	found = []
	for function in ast.walk(tree):
		if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
			continue
		alias = {}
		for node in ast.walk(function):
			if isinstance(node, ast.Assign) and isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name) \
					and node.value.value.id == "self" and node.value.attr in slot_attributes:
				for target in node.targets:
					if isinstance(target, ast.Name):
						alias[target.id] = node.value.attr
		for node in ast.walk(function):
			if not isinstance(node, ast.Attribute):
				continue
			owner, slot = node.value, None
			if isinstance(owner, ast.Name) and owner.id in alias:
				slot = alias[owner.id]
			elif isinstance(owner, ast.Attribute) and isinstance(owner.value, ast.Name) and owner.value.id == "self" \
					and owner.attr in slot_attributes:
				slot = owner.attr
			if slot is not None and node.attr not in slot_attributes[slot]:
				found.append((first_line + node.lineno, slot, node.attr))
	return found


def check_state_reaches(pkg, spec, problems):
	slot_attributes = {}
	for slot, state_class in (("world", spec.world_state), ("seat", spec.seat_state)):
		if state_class is not None:
			slot_attributes[slot] = state_attributes(state_class)
	if not slot_attributes:
		return
	for part_class in spec.implementation.PARTS.values():
		for line, slot, name in sorted(set(state_reaches(part_class, slot_attributes))):
			problems.append("%s.%s: self.%s.%s is not a member of %s (line %d)" % (
				pkg, part_class.__name__, slot, name, getattr(spec, slot + "_state").__name__, line))


def check_agent_parts(problems):
	"""`parts.<name>.<member>`, `economy.parts.<name>.<member>` and `<port>.parts.<name>.<member>` in sim/markets against AgentParts
	(sim/markets/port_parts.py), a plain holder of parts built in its __init__: the member must exist on the class `<name>` is built from."""
	from sim.markets.port_parts import AgentParts
	classes = member_classes(AgentParts)
	for path in sorted(glob.glob("sim/markets/*.py")):
		with open(path, encoding="utf-8") as handle:
			tree = ast.parse(handle.read(), path)
		for node in ast.walk(tree):
			if not (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) and node.value.attr in classes):
				continue
			holder = node.value.value
			is_holder = (isinstance(holder, ast.Name) and holder.id == "parts") or (
				isinstance(holder, ast.Attribute) and holder.attr == "parts" and isinstance(holder.value, (ast.Name, ast.Attribute))
				and (holder.value.id if isinstance(holder.value, ast.Name) else holder.value.attr).lstrip("_") in ("economy", "port"))
			klass = classes[node.value.attr]
			if is_holder and node.attr not in attributes_of(klass):
				problems.append("%s:%d: parts.%s.%s is not defined by %s" % (path, node.lineno, node.value.attr, node.attr, klass.__name__))


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
		check_state_reaches(pkg, spec, problems)
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
				if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) and node.value.attr == "parts" \
						and isinstance(node.value.value, ast.Name) and node.value.value.id == "self" \
						and node.attr not in parts and not node.attr.startswith("__"):
					problems.append("%s.%s: self.parts.%s is not a part (line %d)" % (pkg, part_class.__name__, node.attr, node.lineno))
				if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) \
						and isinstance(node.value.value, ast.Attribute) and node.value.value.attr == "parts" \
						and isinstance(node.value.value.value, ast.Name) and node.value.value.value.id == "self":
					target, member = node.value.attr, node.attr
					if target in parts and member not in attributes_of(parts[target]):
						problems.append("%s.%s: self.parts.%s.%s is not defined (line %d)" % (
							pkg, part_class.__name__, target, member, node.lineno))
				if isinstance(node, ast.Attribute) and not node.attr.startswith("__") and isinstance(node.value, ast.Attribute) \
						and isinstance(node.value.value, ast.Attribute) and isinstance(node.value.value.value, ast.Attribute) \
						and node.value.value.value.attr == "parts" and isinstance(node.value.value.value.value, ast.Name) \
						and node.value.value.value.value.id == "self":
					target, member = node.value.value.attr, node.value.attr
					klass = member_classes(parts[target]).get(member) if target in parts else None
					if klass is not None and node.attr not in attributes_of(klass):
						problems.append("%s.%s: self.parts.%s.%s.%s is not defined by %s (line %d)" % (
							pkg, part_class.__name__, target, member, node.attr, klass.__name__, node.lineno))


def main(names):
	if not os.path.isdir("data"):
		print("data/ is not next to sim/ in %s: every module fails to import without it (MapDataError); run from a checkout with data/" % os.getcwd())
		return 2
	problems = []
	packages = names or sorted(os.path.basename(os.path.dirname(path)) for path in glob.glob("sim/*/module_spec.py"))
	for pkg in packages:
		try:
			check_module(pkg, problems)
		except Exception as error:  # an import failure is a finding
			problems.append("%s: %s: %s" % (pkg, type(error).__name__, error))
	if not names:
		check_private_reaches(problems)
		check_agent_parts(problems)
	for line in problems:
		print(line)
	return 1 if problems else 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
