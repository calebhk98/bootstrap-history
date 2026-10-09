"""The labour object keeps no state of one seat: one labour pool serves every seat, so anything it remembers
between calls must be keyed by what it was computed from or be a year's scratch figure set and read in one
world phase. A new remembered attribute fails here until it is listed with its reason."""

QUICK_TOPIC = True

import ast
import pathlib

from .harness import check

labour_folder = pathlib.Path(__file__).resolve().parents[1] / "labour"
# attribute -> why one object serves every seat
ALLOWED = {
    "_world": "the engine adapter, which reads the acting seat at call time",
    "_need_shares_cache": "keyed by the technologies reached, so a different seat's set recomputes",
    "_clearing_hours_this_year": "set and read inside the one world phase that sizes the farm workforce",
    "_wage_schedule_cache": "keyed by the world economy's tightness factors, which no seat holds",
    "_labour": "the market's back-reference to its labour object",
}
assigned = {}
for path in sorted(labour_folder.glob("*.py")):
    if path.name in ("wages.py",):
        continue   # a pure table of training premia built once from tree data
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, (ast.AugAssign, ast.AnnAssign)) else []
        for target in targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self" \
                    and target.attr.startswith("_"):
                assigned.setdefault(target.attr, []).append("%s:%d" % (path.name, node.lineno))
unlisted = {name: where for name, where in assigned.items() if name not in ALLOWED}
check("the labour object remembers nothing between calls except the listed, seat-safe attributes", not unlisted, unlisted)
check("each listed attribute is still assigned somewhere", set(ALLOWED) <= set(assigned) | {"_world"}, sorted(set(ALLOWED) - set(assigned)))
