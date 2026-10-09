"""No code reads a seat-owned field through the world economy or scenario (scans every module, so not a quick topic)."""
import ast
import dataclasses
import pathlib
import re

from .harness import *  # noqa: F401,F403
from sim.engine.state_holdings import HoldingsState, SeatProgressState

HELD_ECONOMY_FIELDS = {f.name for f in dataclasses.fields(HoldingsState)}
SEAT_SCENARIO_FIELDS = {f.name for f in dataclasses.fields(SeatProgressState)}
root = pathlib.Path(__file__).resolve().parents[1]
pattern = re.compile(r"state\.economy\.(%s)\b|state\.scenario\.(%s)\b" % (
    "|".join(sorted(HELD_ECONOMY_FIELDS)), "|".join(sorted(SEAT_SCENARIO_FIELDS))))
offenders = []
for path in sorted(root.rglob("*.py")):
    if path.name == pathlib.Path(__file__).name:
        continue
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if pattern.search(line):
            offenders.append("%s:%d" % (path.relative_to(root), number))
check("no code reads a holder-owned field through state.economy or state.scenario", not offenders, offenders[:10])


def _is_world_part(node):
    """True for an expression ending in `.economy` or `.scenario` (the world parts of the state)."""
    return isinstance(node, ast.Attribute) and node.attr in ("economy", "scenario")


def _held_names(kind):
    return HELD_ECONOMY_FIELDS if kind == "economy" else SEAT_SCENARIO_FIELDS


aliased = []
for path in sorted(root.rglob("*.py")):
    if path.name == pathlib.Path(__file__).name:
        continue
    tree = ast.parse(path.read_text())
    for function in (n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
        bound = {}
        for node in ast.walk(function):
            if isinstance(node, ast.Assign) and _is_world_part(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        bound[target.id] = node.value.attr
        for node in ast.walk(function):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in bound \
                    and node.attr in _held_names(bound[node.value.id]):
                aliased.append("%s:%d" % (path.relative_to(root), node.lineno))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("getattr", "setattr", "hasattr") \
                    and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                owner = node.args[0]
                kind = owner.attr if _is_world_part(owner) else bound.get(owner.id) if isinstance(owner, ast.Name) else None
                if kind and node.args[1].value in _held_names(kind):
                    aliased.append("%s:%d" % (path.relative_to(root), node.lineno))
check("no function reads a holder-owned field through a local bound to the world economy or scenario",
      not aliased, aliased[:10])
