"""A foreign country's pay, output and prices come from its own part of the economy, never a home answer scaled by a
profile's wage, price or population level (Complaint 407). A scan of the source, so not a game."""

QUICK_TOPIC = True

import ast
import pathlib

from .harness import check

root = pathlib.Path(__file__).resolve().parents[1]
LEVELS = {"wage_index", "price_index"}
# where a country profile's levels may be read: building the profile and its record
PROFILE_LEVEL_READERS = {"agents/cast.py", "agents/records.py"}
# the helpers that used to scale a home answer
REMOVED = {"_relative", "_home_profile"}

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
check("no module reads a profile's wage or price level", not offenders, offenders)

tree = ast.parse((root / "agents" / "country_view.py").read_text())
class_node = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "CountryWorld")
methods = {method.name: method for method in class_node.body if isinstance(method, ast.FunctionDef)}
check("the country view has no helper that scales a home answer", not REMOVED & set(methods), sorted(REMOVED & set(methods)))
shared_figures = []
for name in ("pay_per_person_year", "society_output", "subsistence_cost_per_person_year", "need_floor_costs_per_person_year"):
    reads_shared = any(isinstance(node, ast.Attribute) and node.attr == "_shared" for node in ast.walk(methods[name]))
    if reads_shared:
        shared_figures.append(name)
check("pay, output and cost figures never read the shared (home) world", not shared_figures, shared_figures)
