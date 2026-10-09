"""A foreign country's pay, output and prices come from its own part of the economy. The only place a profile's
wage, price or population level scales a home answer is the labelled fallback in `CountryWorld`, behind a check
for the country's own economy first (Complaint 407). A scan of the source, so not a game."""

QUICK_TOPIC = True

import ast
import pathlib

from .harness import check

root = pathlib.Path(__file__).resolve().parents[1]
LEVELS = {"wage_index", "price_index"}
# where a country profile's levels may be read: building the profile, its record and the fallback itself
PROFILE_LEVEL_READERS = {"agents/country_view.py", "agents/cast.py", "agents/records.py"}

offenders = []
for path in sorted(root.rglob("*.py")):
    relative = path.relative_to(root).as_posix()
    if relative.startswith("tests/") or relative in PROFILE_LEVEL_READERS:
        continue
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in LEVELS:
            holder = node.value
            name = holder.id if isinstance(holder, ast.Name) else holder.attr if isinstance(holder, ast.Attribute) else ""
            if name.endswith("profile") or name == "home":
                offenders.append("%s:%d" % (relative, node.lineno))
check("no module outside the country view reads a profile's wage or price level", not offenders, offenders)

tree = ast.parse((root / "agents" / "country_view.py").read_text())
class_node = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "CountryWorld")
unguarded = []
for method in class_node.body:
    if not isinstance(method, ast.FunctionDef) or method.name == "_relative":
        continue
    calls = [call for call in ast.walk(method) if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)]
    scales = [call for call in calls if call.func.attr == "_relative"]
    asks_economy = any(call.func.attr == "_own_economy" for call in calls)
    if scales and not asks_economy:
        unguarded.append(method.name)
check("every method that scales a home answer by a profile level asks the country's own economy first",
      not unguarded, unguarded)
labelled = []
for method in class_node.body:
    if isinstance(method, ast.FunctionDef) and any(
            isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == "_relative"
            for call in ast.walk(method)):
        labelled.append((method.name, "TEMPORARY HEURISTIC" in (ast.get_docstring(method) or "")))
check("the scaling fallbacks are labelled temporary heuristics", labelled and all(flag for _name, flag in labelled), labelled)
