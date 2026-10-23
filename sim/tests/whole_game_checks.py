"""Lists the test modules that build a whole game and do not say so (Complaint 640).

`python3 -m sim.tests --whole-game-checks` prints each such module, then the counts, and exits non-zero when the
list differs from `whole_game_leftovers.txt`. A rule test calls the rule on inputs it builds; a module that builds a
whole game is a named scenario (file name ends `_scenario`, or the module docstring opens with `SCENARIO`), a baseline
validation (ends `_validation`, or the docstring opens with `BASELINE VALIDATION`, CLAUDE.md 4.2) or a smoke test (ends
`_smoke`, or the docstring opens with `SMOKE`). Anything else that builds a game is either converted to a rule test or listed
in `whole_game_leftovers.txt` with its conversion cost in Complaint 640. The list may only shrink: a module not in
it fails, and a listed module that is declared or no longer builds a game fails too, so the list stays true.

This reads the syntax tree and runs nothing. A module "builds a whole game" when it calls one of BUILDERS by name
(`sim(...)`, `harness.sim(...)`, `S.Sim(...)`), or drives the CLI in process (`proto(...)`, `cli_in_process.run(...)`).
A module that defines its own function of a builder's name, or takes one as a parameter, is not charged for calls to it.
"""
import ast
import os

from sim.tests.discovery import TESTS_DIR, discover_topics

DECLARED_SUFFIXES = ("_scenario", "_validation", "_smoke")
DECLARED_OPENINGS = ("SCENARIO", "BASELINE VALIDATION", "SMOKE")
BUILDERS = {"sim", "unopened_sim", "build_unopened", "Sim", "proto", "spin_up", "spin_up_trace", "spin_up_settled",
            "spin_up_state", "spin_up_result", "spin_up_years", "spin_up_line"}
CLI_MODULES = {"cli_in_process"}
PREFILTER = ("sim(", "Sim(", "proto(", "cli_in_process", "spin_up", "build_unopened")  # parse only files that might build
LEFTOVERS_PATH = os.path.join(TESTS_DIR, "whole_game_leftovers.txt")


def is_declared(topic, source=""):
    """True when the topic's name or its docstring's opening says it is a scenario, a validation or a smoke test."""
    if topic.endswith(DECLARED_SUFFIXES):
        return True
    docstring = ast.get_docstring(ast.parse(source)) or ""
    return docstring.lstrip().startswith(DECLARED_OPENINGS)


def game_builds(source, path="<source>"):
    """[(line, name)] for each call in the source that builds a whole game."""
    tree = ast.parse(source, filename=path)
    own_definitions = {node.name for node in ast.walk(tree)
                       if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in BUILDERS}
    parameters = {argument.arg for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.Lambda))
                  for argument in node.args.args + node.args.kwonlyargs}
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Name):
            name = function.id
            if name in BUILDERS and name not in own_definitions and name not in parameters:
                found.append((node.lineno, name))
        elif isinstance(function, ast.Attribute) and isinstance(function.value, ast.Name):
            owner_name = function.value.id
            if function.attr == "run" and owner_name in CLI_MODULES:
                found.append((node.lineno, "cli_in_process.run"))
            elif function.attr in BUILDERS and function.attr not in own_definitions:
                found.append((node.lineno, "%s.%s" % (owner_name, function.attr)))
    return sorted(found)


def undeclared_modules(tests_dir=TESTS_DIR):
    """{topic: first build as (line, name)} for each undeclared topic that builds a whole game."""
    found = {}
    for topic in discover_topics(tests_dir):
        path = os.path.join(tests_dir, "test_%s.py" % topic)
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        if topic.endswith(DECLARED_SUFFIXES) or not any(name in source for name in PREFILTER):
            continue
        if is_declared(topic, source):
            continue
        builds = game_builds(source, path)
        if builds:
            found[topic] = builds[0]
    return found


def listed_leftovers(path=LEFTOVERS_PATH):
    """Topics named in the leftovers file (one per line; `#` starts a comment)."""
    with open(path, encoding="utf-8") as handle:
        lines = [line.split("#")[0].strip() for line in handle]
    return {line for line in lines if line}


def differences(found, listed):
    """(new, stale): undeclared builders the list lacks, and listed topics that no longer are one."""
    return sorted(set(found) - set(listed)), sorted(set(listed) - set(found))


def report():
    found = undeclared_modules()
    new, stale = differences(found, listed_leftovers())
    for topic in sorted(found):
        line, name = found[topic]
        print("%-8s %s:%d  %s" % ("NEW" if topic in new else "listed", topic, line, name))
    for topic in stale:
        print("STALE    %s (declared, gone or no longer builds a game: remove it from whole_game_leftovers.txt)" % topic)
    print("\nundeclared modules that build a whole game: %d (%d not in the leftovers list, %d stale list entries)"
          % (len(found), len(new), len(stale)))
    return len(new) + len(stale)
