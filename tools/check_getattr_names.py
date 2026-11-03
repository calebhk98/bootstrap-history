"""getattr/hasattr/setattr probes whose literal name nothing defines. Run from the repository root.

For every `getattr(obj, "name"...)`, `hasattr(obj, "name")` and `setattr(obj, "name", ...)` in sim/ and mods/ (tests excluded) the check
collects every name the code base defines: functions and methods (also properties), classes, names assigned at module or class level,
annotated fields (dataclass, NamedTuple), `<anything>.name = ...` and `<anything>.__dict__["name"] = ...` assignments (instance
attributes), imported names, command-line options (`add_argument("--save-winner")` defines `save_winner` on the parsed namespace), and
names written by a `setattr(..., "name", ...)` with the same literal. A probe whose name is defined nowhere can never succeed, so only its default is ever
used: typically the method moved to a part and the probe was not renamed. Dunder names are skipped, and a name in ALLOWED below is skipped.
Prints `file:line: <call> of "<name>" ...` per problem and exits 1 when there is any."""
import ast
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBES = ("getattr", "hasattr", "setattr")

# Names that are genuinely optional and defined outside this code base (a standard library or third-party attribute, or a mod hook
# looked up by name). Give each a reason. Starts empty.
ALLOWED = {}


def source_files():
	for top in ("sim", "mods"):
		for path in sorted(glob.glob(os.path.join(ROOT, top, "**", "*.py"), recursive=True)):
			relative = os.path.relpath(path, ROOT)
			if relative.startswith("sim/tests/") or "__pycache__" in relative:
				continue
			yield relative


def literal_name(call):
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


def collect(trees):
	defined = set()
	probes = []
	for relative, tree in trees.items():
		for node in ast.walk(tree):
			if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
				defined.add(node.name)
			elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
				defined.add(node.id)
			elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
				defined.add(node.attr)
			elif isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Store):
				if isinstance(node.value, ast.Attribute) and node.value.attr == "__dict__" and isinstance(node.slice, ast.Constant):
					defined.add(node.slice.value)
			elif isinstance(node, (ast.Import, ast.ImportFrom)):
				for alias in node.names:
					defined.add((alias.asname or alias.name).split(".")[0])
			elif isinstance(node, ast.Call):
				if isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
					defined.update(option_names(node))
				found = literal_name(node)
				if found:
					probes.append((relative, node.lineno, found[0], found[1]))
					if found[0] == "setattr":
						defined.add(found[1])
	return defined, probes


def main():
	trees = {}
	for relative in source_files():
		with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
			trees[relative] = ast.parse(handle.read(), relative)
	defined, probes = collect(trees)
	problems = 0
	for relative, line, kind, name in probes:
		if name in defined or name in ALLOWED or (name.startswith("__") and name.endswith("__")):
			continue
		print(f'{relative}:{line}: {kind} of "{name}" which nothing in sim/ or mods/ defines (renamed or moved?)')
		problems += 1
	return 1 if problems else 0


if __name__ == "__main__":
	sys.exit(main())
