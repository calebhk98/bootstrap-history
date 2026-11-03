"""getattr/hasattr/setattr probes with a literal name that nothing justifies. Run from the repository root.

A `getattr(obj, "name", ...)`, `hasattr(obj, "name")` or `setattr(obj, "name", ...)` in sim/ and mods/ (tests excluded) is allowed only when
  (a) the name is in OPTIONAL below (or in OPTIONAL_IN_FILE for that file): a hook that some implementations define and others do not, each with who defines it and why a plain
      read would be wrong; or the name is a command-line option read off a parsed `args` / `namespace`; or
  (b) the receiver's class can be resolved statically and that class (or a base) defines the name. A receiver resolves when it is `self`
      in a class, a parameter with an annotation naming a class, a local assigned once from `Class(...)`, a `self.<attribute>` annotated
      with or only ever assigned from one class (or from a parameter annotated with one), or a chain of such attributes. A class defines a
      name by a method, a class-level name, an annotated field (dataclass, NamedTuple) or a `self.<name>` assignment in its methods.
Everything else is reported: the receiver is of unknown type, or its class lacks the name (typically a method that moved to a part or to
another object, so only the default is ever used). Locals and `x.attr = ...` stores elsewhere do not define a name for this check, and a
`setattr` does not define the name it writes. A class with `__getattr__` or with a base that cannot be found is never proven to define
anything. Dunder names are skipped.
Prints `file:line: literal <call> of <name> on a receiver whose class is unknown or lacks it ...` per problem and exits 1 when there is any."""
import ast
import builtins
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from class_index import Index  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBES = ("getattr", "hasattr", "setattr")
ARGUMENT_RECEIVERS = {"args", "namespace", "parsed", "options"}

# Genuinely optional hooks: the probe's name, who defines it, why a plain read would be wrong. A name here is allowed on any receiver.
OPTIONAL = {
	"research_hands": "defined by a researcher-like actor (sim/projects/researcher.py) and a country crew (sim/agents/country_state_crew.py); other actors do no research",
	"rivals_of": "callback field of the actors that run concerns in the shared market (sim/agents/firm.py, player.py), which the registry installs; the registry probes any actor's class for it to find them",
	"on_capacity_change": "callback installed on firms by the registry (sim/agents/firm.py); absent on an actor with no registry",
	"find_actor": "callback installed by the registry on firms and players (sim/agents/firm.py, player.py); absent on an actor with no registry",
	"command_table": "table installed by the registry on players (sim/agents/player.py); absent on actors that take no commands",
	"proven_concerns": "defined by actors that run concerns (sim/agents/player.py, registry_concerns.py); a country or household has none",
	"aware": "the awareness map of actors that keep one (sim/agents/records.py, base.py); a party stub has none",
	"purses": "the purse book of ledger-backed parties (sim/agents/purses.py); a party outside the ledger has none",
	"stands_at_home": "class flag of a seat's party and account (sim/agents/household_party.py, sim/ledger/seat_account.py); other parties do not carry coin",
	"input_share": "method of owners with plants of their own (sim/agents/government_enterprises.py); other owners have no enterprises part",
	"ui_readable": "attribute set by the decorator that marks a method readable by the UI (sim/engine/readable.py); an undecorated method lacks it",
	"register": "optional entry point of a mod's code module (sim/engine/mod_code.py); a module without it registers nothing",
	"receiver_tile": "field of money moves that cross tiles (sim/book.py); a plain move lacks it",
	"enterprises": "part of an owner with plants of its own (sim/agents/government.py); a firm or a player owner has none",
	"part_name": "attribute set on a forwarding method (sim/assembly/assemble.py _part_forwarder); a method the module class defines itself lacks it",
	"_guard_view": "set on the copies the read guard hands out (sim/assembly/read_guard.py); a plain dict, list or set lacks it",
	"location": "method of actors and seat parties (sim/agents/base.py, household_party.py); an edge (a named account, sim/agents/edges.py) has none",
	"record": "the record of an actor or a seat (sim/agents/base.py, household_party.py); an edge or a bare party has none",
	"keys": "a payment's purpose is a mapping of label to share or a single label (sim/coin/rules.py); a label has no keys",
	"OWNERS": "class constant of the economy record's part classes (sim/economy/*_record.py); a table field's type (a Dict[...]) has none",
	"to_canon_dict": "defined by the few saved classes with a canonical form; serialize_state meets arbitrary objects (sim/engine/state.py)",
}

# Names allowed only in one file: the probes of a reply that may be plain text, which only that file reads.
OPTIONAL_IN_FILE = {
	"sim/refusal.py": {
		"cause": "attribute of a Refusal; the reply probed may be plain text",
		"facts": "attribute of a Refusal; the reply probed may be plain text",
		"choices": "attribute of a Refusal; the reply probed may be plain text",
	},
}


def source_files():
	for top in ("sim", "mods"):
		for path in sorted(glob.glob(os.path.join(ROOT, top, "**", "*.py"), recursive=True)):
			relative = os.path.relpath(path, ROOT)
			if relative.startswith("sim/tests/") or "__pycache__" in relative:
				continue
			yield relative


def literal_probe(call):
	"""(kind, name) for a probe with a literal name, else None."""
	if isinstance(call.func, ast.Name) and call.func.id in PROBES and len(call.args) >= 2:
		argument = call.args[1]
		if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
			return call.func.id, argument.value
	return None


def option_names(call):
	"""The attribute names an argparse `add_argument` call creates on the parsed namespace."""
	for keyword in call.keywords:
		if keyword.arg == "dest" and isinstance(keyword.value, ast.Constant):
			return {keyword.value.value}
	flags = [argument.value for argument in call.args if isinstance(argument, ast.Constant) and isinstance(argument.value, str)]
	long_flags = [flag for flag in flags if flag.startswith("--")]
	chosen = long_flags[0] if long_flags else (flags[0] if flags else "")
	return {chosen.lstrip("-").replace("-", "_")} if chosen else set()


def functions_in(body):
	return [item for item in body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]


class Facts:
	"""What the classes of the code base define and what their attributes hold, resolved through each file's own imports."""

	def __init__(self, index):
		self.index = index
		self.members = {}
		self.attribute_types = {}

	@staticmethod
	def key(module_name, node):
		return (module_name, node.name, node.lineno)

	def self_name(self, function):
		"""The first parameter's name of a method (`self`, or `cls` for a classmethod), else None."""
		if any(isinstance(d, ast.Name) and d.id == "staticmethod" for d in function.decorator_list):
			return None
		arguments = function.args.posonlyargs + function.args.args
		return arguments[0].arg if arguments else None

	def annotation_class(self, module_name, annotation):
		"""The (module, ClassDef) an annotation names, looking through Optional[...], `X | None` and a quoted name; else None."""
		if annotation is None:
			return None
		if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
			try:
				annotation = ast.parse(annotation.value, mode="eval").body
			except SyntaxError:
				return None
		if isinstance(annotation, ast.Subscript):
			if ast.unparse(annotation.value).split(".")[-1] == "Optional":
				return self.annotation_class(module_name, annotation.slice)
			return None
		if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
			sides = [side for side in (annotation.left, annotation.right) if not (isinstance(side, ast.Constant) and side.value is None)]
			return self.annotation_class(module_name, sides[0]) if len(sides) == 1 else None
		found = self.index.resolve(module_name, annotation)
		return (found[1], found[2]) if found is not None and found[0] == "class" else None

	def bases_of(self, module_name, node):
		"""[(module, ClassDef) or builtin type] for each base; None when one cannot be found."""
		bases = []
		for base in node.bases:
			if isinstance(base, ast.Subscript):
				base = base.value
			found = self.index.resolve(module_name, base)
			if found is not None and found[0] == "class":
				bases.append((found[1], found[2]))
			elif isinstance(base, ast.Name) and isinstance(getattr(builtins, base.id, None), type) and not self.rebound(module_name, base.id):
				bases.append(getattr(builtins, base.id))
			else:
				return None
		return bases

	def rebound(self, module_name, name):
		module = self.index.modules[module_name]
		return name in module.bound or name in module.imports or name in module.classes

	def own_members(self, module_name, node):
		"""Names the class body and its methods define for instances."""
		names = set()
		for item in node.body:
			if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
				names.add(item.name)
			elif isinstance(item, ast.Assign):
				names |= {name.id for target in item.targets for name in ast.walk(target) if isinstance(name, ast.Name)}
			elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
				names.add(item.target.id)
		for function in functions_in(node.body):
			me = self.self_name(function)
			for inner in ast.walk(function):
				if isinstance(inner, ast.Attribute) and isinstance(inner.ctx, ast.Store) and isinstance(inner.value, ast.Name) \
						and inner.value.id == me and me is not None:
					names.add(inner.attr)
		return names

	def defines(self, module_name, node, name, seen=None):
		"""True when the class or a base defines `name`; False when it provably does not; None when it cannot be told."""
		seen = seen if seen is not None else set()
		key = self.key(module_name, node)
		if key in seen:
			return False
		seen.add(key)
		if key not in self.members:
			self.members[key] = self.own_members(module_name, node)
		own = self.members[key]
		if name in own:
			return True
		if "__getattr__" in own or "__getattribute__" in own:
			return None
		bases = self.bases_of(module_name, node)
		if bases is None:
			return None
		unknown = False
		for base in bases:
			if isinstance(base, type):
				if hasattr(base, name):
					return True
				continue
			found = self.defines(base[0], base[1], name, seen)
			if found:
				return True
			unknown = unknown or found is None
		return None if unknown else False

	def attribute_class(self, module_name, node, attribute):
		"""The class a `self.<attribute>` of this class holds: annotated, or assigned from one class only; else None."""
		key = (self.key(module_name, node), attribute)
		if key in self.attribute_types:
			return self.attribute_types[key]
		self.attribute_types[key] = None
		found = self._attribute_class(module_name, node, attribute)
		self.attribute_types[key] = found
		return found

	def _attribute_class(self, module_name, node, attribute):
		candidates = set()
		for item in node.body:
			if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == attribute:
				return self.annotation_class(module_name, item.annotation)
		for function in functions_in(node.body):
			me = self.self_name(function)
			parameters = {argument.arg: argument for argument in function.args.posonlyargs + function.args.args + function.args.kwonlyargs}
			for inner in ast.walk(function):
				targets = []
				if isinstance(inner, ast.Assign):
					targets, value, annotation = inner.targets, inner.value, None
				elif isinstance(inner, ast.AnnAssign):
					targets, value, annotation = [inner.target], inner.value, inner.annotation
				else:
					continue
				for target in targets:
					if not (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == me
					        and target.attr == attribute and me is not None):
						continue
					if annotation is not None:
						return self.annotation_class(module_name, annotation)
					if isinstance(value, ast.Call):
						found = self.index.resolve(module_name, value.func)
						candidates.add((found[1], found[2]) if found is not None and found[0] == "class" else None)
					elif isinstance(value, ast.Name) and value.id in parameters:
						candidates.add(self.annotation_class(module_name, parameters[value.id].annotation))
					else:
						candidates.add(None)
		if len(candidates) == 1:
			return next(iter(candidates))
		return None


class Visitor:
	def __init__(self, facts, module, options):
		self.facts = facts
		self.relative, self.module_name, self.tree = module.path, module.name, module.tree
		self.options = options
		self.problems = []
		self.parents = {}
		for parent in ast.walk(self.tree):
			for child in ast.iter_child_nodes(parent):
				self.parents[child] = parent

	def scopes_of(self, node):
		"""The enclosing functions, innermost first."""
		found = []
		node = self.parents.get(node)
		while node is not None:
			if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
				found.append(node)
			node = self.parents.get(node)
		return found

	def class_of_method(self, function):
		parent = self.parents.get(function)
		return parent if isinstance(parent, ast.ClassDef) else None

	def stores_of(self, function, name):
		stores = []
		for inner in ast.walk(function):
			if isinstance(inner, ast.Name) and inner.id == name and isinstance(inner.ctx, (ast.Store, ast.Del)):
				stores.append(inner)
		return stores

	def class_of_name(self, name, scopes):
		"""The (module, ClassDef) a plain name in these scopes holds, else None."""
		for function in scopes:
			if isinstance(function, ast.Lambda):
				if name in {argument.arg for argument in function.args.args}:
					return None
				continue
			arguments = function.args.posonlyargs + function.args.args + function.args.kwonlyargs
			me = self.facts.self_name(function)
			owner = self.class_of_method(function)
			if owner is not None and me == name and name in ("self", "cls"):
				return (self.module_name, owner)
			if name in {argument.arg for argument in arguments}:
				if self.stores_of(function, name):
					return None
				argument = next(argument for argument in arguments if argument.arg == name)
				return self.facts.annotation_class(self.module_name, argument.annotation)
			stores = self.stores_of(function, name)
			if stores:
				if len(stores) != 1:
					return None
				statement = self.parents.get(stores[0])
				if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Call):
					found = self.facts.index.resolve(self.module_name, statement.value.func)
					return (found[1], found[2]) if found is not None and found[0] == "class" else None
				if isinstance(statement, ast.AnnAssign):
					return self.facts.annotation_class(self.module_name, statement.annotation)
				return None
		return None

	def class_of(self, expression, scopes):
		if isinstance(expression, ast.Name):
			return self.class_of_name(expression.id, scopes)
		if isinstance(expression, ast.Call):
			found = self.facts.index.resolve(self.module_name, expression.func)
			return (found[1], found[2]) if found is not None and found[0] == "class" else None
		if isinstance(expression, ast.Attribute):
			owner = self.class_of(expression.value, scopes)
			if owner is None:
				return None
			return self.facts.attribute_class(owner[0], owner[1], expression.attr)
		return None

	def judge(self, call, kind, name):
		if name.startswith("__") and name.endswith("__") or name in OPTIONAL or name in OPTIONAL_IN_FILE.get(self.relative, {}):
			return
		receiver = call.args[0]
		if isinstance(receiver, ast.Name) and receiver.id in ARGUMENT_RECEIVERS and name in self.options:
			return
		owner = self.class_of(receiver, self.scopes_of(call))
		if owner is not None and self.facts.defines(owner[0], owner[1], name):
			return
		self.problems.append(
			'%s:%d: literal %s of %s on a receiver whose class is unknown or lacks it (%s); use a plain read or add it to the optional list with a reason'
			% (self.relative, call.lineno, kind, name, ast.unparse(receiver)))

	def run(self):
		for node in ast.walk(self.tree):
			if isinstance(node, ast.Call):
				probe = literal_probe(node)
				if probe:
					self.judge(node, *probe)
		return self.problems


def main():
	index = Index(ROOT)
	options = set()
	for module in index.modules.values():
		for node in ast.walk(module.tree):
			if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
				options |= option_names(node)
	facts = Facts(index)
	problems = list(index.parse_errors)
	for module in index.modules.values():
		problems += Visitor(facts, module, options).run()
	for line in sorted(problems):
		print(line)
	return 1 if problems else 0


if __name__ == "__main__":
	sys.exit(main())
