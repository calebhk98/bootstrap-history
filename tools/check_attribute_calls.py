"""Attributes read from an adapter object that the adapter's class does not define. Run from the repository root.

An adapter is a class whose instances are handed to other code in place of the game (`world`, `sim`, `reads`): every class in a file
named `world*.py` or `port_world*.py` under `sim/`, and every class named `...World` or `...Reads` outside a `state.py` (the
saved-state sections). Nothing is imported; the files are parsed with `ast`.

For each adapter class the check follows where an instance goes:
  1. a binding of `Adapter(...)` to a name or to `self.<attribute>`; `self` inside the adapter class is the adapter;
  2. each call that receives such a binding as an argument: the callee's parameter (a class's `__init__` parameter, a function's)
     becomes a binding of the same adapter, and `self.<attribute> = <parameter>` in the callee's class binds that attribute;
  3. the names found this way are then checked in every function or class of the files that receive the adapter.
An attribute read on a binding that is not a method, class attribute, property, or `self.<attribute>` assignment of the adapter class (or
a base) is reported, as is one read on a sub-reader the adapter builds (`self.state = StateReads(...)`). Heuristic: an adapter
whose instance leaves through a factory, a `return` or a lambda is followed by the names `world`, `_world`, `reads` and `sim` in the
files of its own package. A class with `__getattr__`, or a base that cannot be found, is not checked.
Prints `file:line: <binding>.<attribute> is not defined by <Adapter>` per problem and exits 1 when there is any."""
import ast
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FALLBACK_NAMES = ("world", "_world", "reads", "sim")
ADAPTER_FILES = ("world", "port_world")
NEUTRAL_BASES = {"object", "Protocol", "Generic", "ABC"}
OBJECT_NAMES = set(dir(object))


def source_files():
	for path in sorted(glob.glob(os.path.join(ROOT, "sim", "**", "*.py"), recursive=True)):
		relative = os.path.relpath(path, ROOT)
		if relative.startswith("sim/tests/") or "__pycache__" in relative:
			continue
		yield relative


def parse_all():
	trees = {}
	for relative in source_files():
		with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
			trees[relative] = ast.parse(handle.read(), relative)
	return trees


def is_adapter_name(name, relative):
	base = os.path.basename(relative)
	if base == "state.py":
		return False
	return any(base.startswith(prefix) for prefix in ADAPTER_FILES) or name.endswith(("World", "Reads"))


class ClassInfo:
	def __init__(self, relative, node):
		self.relative = relative
		self.node = node
		self.name = node.name
		self.members = set()
		self.sub_readers = {}
		self.dynamic = False


def collect_classes(trees):
	classes = {}
	for relative, tree in trees.items():
		for node in ast.walk(tree):
			if isinstance(node, ast.ClassDef):
				classes.setdefault(node.name, []).append(ClassInfo(relative, node))
	return classes


def base_names(node):
	names = []
	for base in node.bases:
		if isinstance(base, ast.Subscript):
			base = base.value
		names.append(base.attr if isinstance(base, ast.Attribute) else base.id if isinstance(base, ast.Name) else None)
	return names


def own_members(info, adapter_names):
	"""Fill `members` and `sub_readers` of one class from its own body (bases are folded in by `resolve_members`)."""
	for node in info.node.body:
		if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
			info.members.add(node.name)
			if node.name == "__getattr__":
				info.dynamic = True
		elif isinstance(node, ast.Assign):
			for target in node.targets:
				for name in ast.walk(target):
					if isinstance(name, ast.Name):
						info.members.add(name.id)
		elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
			info.members.add(node.target.id)
	for node in ast.walk(info.node):
		if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and isinstance(node.value, ast.Name) \
				and node.value.id == "self":
			info.members.add(node.attr)
		if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
			called = call_name(node.value)
			if called in adapter_names:
				for target in node.targets:
					if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
						info.sub_readers[target.attr] = called


def call_name(call):
	function = call.func
	if isinstance(function, ast.Name):
		return function.id
	if isinstance(function, ast.Attribute):
		return function.attr
	return None


def resolve_members(info, classes, seen=()):
	"""The class's members with those of its bases; None when a base cannot be found (the class is not checked)."""
	if info.dynamic:
		return None
	members = set(info.members) | OBJECT_NAMES
	for name in base_names(info.node):
		if name in NEUTRAL_BASES:
			continue
		candidates = classes.get(name)
		if not candidates or name in seen:
			return None
		inherited = resolve_members(candidates[0], classes, seen + (name,))
		if inherited is None:
			return None
		members |= inherited
	return members


def key_of(node):
	"""`x` for a Name, `self.x` for a self attribute, else None."""
	if isinstance(node, ast.Name):
		return node.id
	if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
		return "self." + node.attr
	return None


def parameters_of(function):
	arguments = function.args
	return [argument.arg for argument in arguments.posonlyargs + arguments.args], [argument.arg for argument in arguments.kwonlyargs]


class Checker:
	def __init__(self, trees):
		self.trees = trees
		self.classes = collect_classes(trees)
		self.adapter_names = {name for name, infos in self.classes.items()
		                      if any(is_adapter_name(name, info.relative) for info in infos)}
		for infos in self.classes.values():
			for info in infos:
				own_members(info, self.adapter_names)
		self.members = {}
		for name in self.adapter_names:
			for info in self.classes[name]:
				self.members[(info.relative, name)] = resolve_members(info, self.classes)
		self.functions = {}
		for relative, tree in trees.items():
			for node in ast.walk(tree):
				if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
					self.functions.setdefault(node.name, []).append((relative, node))
		self.bindings = {}          # relative file -> {adapter class name: set of (scope node or None, key)}
		self.parents = {}
		self.file_of_tree = {tree: relative for relative, tree in trees.items()}
		for tree in trees.values():
			for node in ast.walk(tree):
				for child in ast.iter_child_nodes(node):
					self.parents[child] = node
		self.escaped = set()        # adapter class names whose instances leave through a return, a lambda or a factory

	def bind(self, relative, adapter, key, scope=None):
		keys = self.bindings.setdefault(relative, {}).setdefault(adapter, set())
		if (scope, key) in keys:
			return False
		keys.add((scope, key))
		return True

	def enclosing(self, node, kinds):
		node = self.parents.get(node)
		while node is not None and not isinstance(node, kinds):
			node = self.parents.get(node)
		return node

	def scope_for(self, node, key):
		"""A `self.<attribute>` binds in its class, a plain name in its function."""
		if key.startswith("self."):
			return self.enclosing(node, ast.ClassDef)
		return self.enclosing(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))

	def file_of(self, node):
		while node in self.parents:
			node = self.parents[node]
		return self.file_of_tree[node]

	def imported_from(self, relative, name):
		"""The file a `from ... import name` in `relative` points at, or None."""
		for node in ast.walk(self.trees[relative]):
			if isinstance(node, ast.ImportFrom) and any((alias.asname or alias.name) == name for alias in node.names):
				parts = relative.split("/")[:-1]
				if node.level:
					parts = parts[:len(parts) - (node.level - 1)] if node.level > 1 else parts
					parts = parts + (node.module.split(".") if node.module else [])
				else:
					parts = (node.module or "").split(".")
				return "/".join(parts)
		return None

	def choose(self, call, candidates):
		"""The one candidate (relative file, definition) the call can mean: the only one, one in the caller's file, or the imported one."""
		if len(candidates) <= 1:
			return list(candidates)
		caller = self.file_of(call)
		local = [entry for entry in candidates if entry[0] == caller]
		if local:
			return local
		source = self.imported_from(caller, call_name(call))
		if source is not None:
			imported = [entry for entry in candidates if entry[0] in (source + ".py", source + "/__init__.py")]
			if len(imported) == 1:
				return imported
		return []

	def without_self(self, function):
		"""The positional parameters a caller fills: a method's first one is the instance."""
		parameters = parameters_of(function)[0]
		return parameters[1:] if isinstance(self.parents.get(function), ast.ClassDef) else parameters

	def callee_parameters(self, call):
		"""[(relative file, class or function node, parameter list without self, keyword names)] a call may reach."""
		name = call_name(call)
		found = []
		if name in self.classes:
			for info in self.choose(call, [(info.relative, info) for info in self.classes[name]]) if isinstance(call.func, ast.Name) \
					else [(info.relative, info) for info in self.classes[name]]:
				info = info[1]
				for node in info.node.body:
					if isinstance(node, ast.FunctionDef) and node.name == "__init__":
						found.append((info.relative, info.node, parameters_of(node)[0][1:], node))
		if isinstance(call.func, ast.Name):
			for relative, node in self.choose(call, self.functions.get(name, ())):
				found.append((relative, None, self.without_self(node), node))
		elif isinstance(call.func, ast.Attribute) and name not in self.classes:
			methods = [(relative, node) for relative, node in self.functions.get(name, ())]
			if len(methods) == 1:
				relative, node = methods[0]
				found.append((relative, None, self.without_self(node), node))
		return found

	def seed(self):
		for relative, tree in self.trees.items():
			parents = {}
			for node in ast.walk(tree):
				for child in ast.iter_child_nodes(node):
					parents[child] = node
			for node in ast.walk(tree):
				if not (isinstance(node, ast.Call) and call_name(node) in self.adapter_names):
					continue
				adapter = call_name(node)
				if isinstance(node.func, ast.Name):
					meant = self.choose(node, [(info.relative, info) for infos in [self.classes[adapter]] for info in infos])
					if not meant or not is_adapter_name(adapter, meant[0][0]):
						continue
				elif not any(is_adapter_name(adapter, info.relative) for info in self.classes[adapter]):
					continue
				parent = parents.get(node)
				if isinstance(parent, ast.Assign) and parent.value is node:
					for target in parent.targets:
						key = key_of(target)
						if key is not None:
							self.bind(relative, adapter, key, self.scope_for(parent, key))
				elif isinstance(parent, ast.Call) and node in parent.args:
					self.bind_argument(parent, parent.args.index(node), None, adapter)
				elif isinstance(parent, ast.keyword) and isinstance(parents.get(parent), ast.Call):
					self.bind_argument(parents[parent], None, parent.arg, adapter)
				elif isinstance(parent, (ast.Return, ast.Lambda)):
					self.escaped.add(adapter)

	def bind_argument(self, call, position, keyword, adapter):
		changed = False
		for relative, class_node, parameters, function in self.callee_parameters(call):
			parameter = None
			if keyword is not None and keyword in parameters + parameters_of(function)[1]:
				parameter = keyword
			elif position is not None and position < len(parameters):
				parameter = parameters[position]
			if parameter is None:
				continue
			changed |= self.bind(relative, adapter, parameter, function)
			if class_node is not None:
				for node in ast.walk(function):
					if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name) and node.value.id == parameter:
						for target in node.targets:
							key = key_of(target)
							if key is not None and key.startswith("self."):
								changed |= self.bind(relative, adapter, key, class_node)
		return changed

	def propagate(self):
		changed = True
		while changed:
			changed = False
			for relative, by_adapter in list(self.bindings.items()):
				tree = self.trees[relative]
				for adapter, keys in list(by_adapter.items()):
					for node in ast.walk(tree):
						if not isinstance(node, ast.Call):
							continue
						for position, argument in enumerate(node.args):
							if self.is_bound(argument, node, keys):
								changed |= self.bind_argument(node, position, None, adapter)
						for keyword in node.keywords:
							if keyword.arg and self.is_bound(keyword.value, node, keys):
								changed |= self.bind_argument(node, None, keyword.arg, adapter)

	def is_bound(self, expression, place, keys):
		key = key_of(expression)
		if key is None:
			return False
		node = place
		while node is not None:
			if (node, key) in keys:
				return True
			node = self.parents.get(node)
		return (None, key) in keys

	def add_fallback(self):
		for adapter in sorted(self.escaped):
			for info in self.classes[adapter]:
				package = os.path.dirname(info.relative)
				for relative in self.trees:
					if os.path.dirname(relative) == package:
						for name in FALLBACK_NAMES:
							self.bind(relative, adapter, name)

	def type_of(self, node, keys_by_adapter, self_adapter):
		"""keys_by_adapter maps each adapter to the keys bound at this place."""
		"""The adapter class an expression is bound to, following sub-readers; None when unknown."""
		if isinstance(node, ast.Name) and node.id == "self":
			return self_adapter
		key = key_of(node)
		if key is not None:
			if key.startswith("self.") and self_adapter is not None:
				return self.sub_reader(self_adapter, key[len("self."):])
			for adapter, keys in keys_by_adapter.items():
				if key in keys:
					return adapter
			return None
		if isinstance(node, ast.Attribute):
			owner = self.type_of(node.value, keys_by_adapter, self_adapter)
			if owner is not None:
				return self.sub_reader(owner, node.attr)
		return None

	def within(self, node, scope):
		while node is not None:
			if node is scope:
				return True
			node = self.parents.get(node)
		return False

	def sub_reader(self, adapter, attribute):
		for info in self.classes[adapter]:
			if attribute in info.sub_readers:
				return info.sub_readers[attribute]
		return None

	def report(self):
		problems = set()
		for relative, tree in self.trees.items():
			self.visit(relative, tree, self.bindings.get(relative, {}), None, problems)
		return sorted(problems)

	def visit(self, relative, node, by_adapter, self_adapter, problems):
		if isinstance(node, ast.ClassDef):
			self_adapter = node.name if node.name in self.adapter_names else None
		if isinstance(node, ast.Attribute) and not node.attr.startswith("__"):
			here = {adapter: {key for scope, key in keys if scope is None or self.within(node, scope)} for adapter, keys in by_adapter.items()}
			owner = self.type_of(node.value, here, self_adapter)
			if owner is not None:
				checked = [self.members[(info.relative, owner)] for info in self.classes[owner]]
				if not any(members is None or node.attr in members for members in checked):
					problems.add("%s:%d: %s.%s is not defined by %s" % (relative, node.lineno, ast.unparse(node.value), node.attr, owner))
		for child in ast.iter_child_nodes(node):
			self.visit(relative, child, by_adapter, self_adapter, problems)


def main():
	checker = Checker(parse_all())
	checker.seed()
	checker.propagate()
	checker.add_fallback()
	checker.propagate()
	problems = checker.report()
	for line in problems:
		print(line)
	return 1 if problems else 0


if __name__ == "__main__":
	sys.exit(main())
