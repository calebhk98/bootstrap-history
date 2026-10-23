"""No code reads a seat-owned field through the world economy or scenario. A source scan: the files that could offend
are found by text first, so only those are parsed."""
QUICK_TOPIC = True

import ast
import dataclasses
import pathlib
import re
import unittest

from sim.engine.state_holdings import HoldingsState, SeatProgressState

HELD_ECONOMY_FIELDS = {field.name for field in dataclasses.fields(HoldingsState)}
SEAT_SCENARIO_FIELDS = {field.name for field in dataclasses.fields(SeatProgressState)}
ROOT = pathlib.Path(__file__).resolve().parents[1]
THIS_FILE = pathlib.Path(__file__).name
PATTERN = re.compile(r"state\.economy\.(%s)\b|state\.scenario\.(%s)\b" % (
    "|".join(sorted(HELD_ECONOMY_FIELDS)), "|".join(sorted(SEAT_SCENARIO_FIELDS))))
# a world part used as a value (bound, or the owner of a getattr), not only read through
BARE_WORLD_PART = re.compile(r"\.(economy|scenario)\b(?!\.)")
HELD_NAMES = sorted(HELD_ECONOMY_FIELDS | SEAT_SCENARIO_FIELDS)


def sources():
    """(path, text) of every module that takes `.economy` or `.scenario` and names a held field; no other can offend."""
    for path in sorted(ROOT.rglob("*.py")):
        if path.name != THIS_FILE:
            text = path.read_text()
            if (".economy" in text or ".scenario" in text) and any(name in text for name in HELD_NAMES):
                yield path, text


def _is_world_part(node):
    """True for an expression ending in `.economy` or `.scenario` (the world parts of the state)."""
    return isinstance(node, ast.Attribute) and node.attr in ("economy", "scenario")


def _held_names(kind):
    return HELD_ECONOMY_FIELDS if kind == "economy" else SEAT_SCENARIO_FIELDS


def aliased_reads(tree):
    """Line numbers of reads of a held field through a local bound to the world economy or scenario."""
    found = []
    if not any(isinstance(node, ast.Assign) and _is_world_part(node.value)
               or isinstance(node, ast.Call) and node.args and _is_world_part(node.args[0]) for node in ast.walk(tree)):
        return found
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
                found.append(node.lineno)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("getattr", "setattr", "hasattr") \
                    and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                owner = node.args[0]
                kind = owner.attr if _is_world_part(owner) else bound.get(owner.id) if isinstance(owner, ast.Name) else None
                if kind and node.args[1].value in _held_names(kind):
                    found.append(node.lineno)
    return found


class HoldingsWallTests(unittest.TestCase):
    def test_no_code_reads_a_holder_owned_field_through_state_economy_or_scenario(self):
        offenders = ["%s:%d" % (path.relative_to(ROOT), number)
                     for path, text in sources() for number, line in enumerate(text.splitlines(), 1) if PATTERN.search(line)]
        self.assertEqual(offenders[:10], [])

    def test_no_function_reads_a_holder_owned_field_through_a_local_bound_to_the_world_economy_or_scenario(self):
        offenders = ["%s:%d" % (path.relative_to(ROOT), number)
                     for path, text in sources() if BARE_WORLD_PART.search(text) for number in aliased_reads(ast.parse(text))]
        self.assertEqual(offenders[:10], [])

    def test_the_scan_finds_an_aliased_read_when_there_is_one(self):
        field = sorted(HELD_ECONOMY_FIELDS)[0]
        tree = ast.parse("def read(game):\n    world = game.state.economy\n    return world.%s\n" % field)
        self.assertEqual(aliased_reads(tree), [3])


if __name__ == "__main__":
    unittest.main()
