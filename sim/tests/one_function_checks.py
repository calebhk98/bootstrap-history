"""Lists the test modules that reach the function under test through other engine functions.

A test calls one function, the one under test, on inputs written out in the test: it builds the state the function
reads (a stand-in, a dict, a dataclass) instead of building a game or an economy and running commands until that state
appears. `python3 -m sim.tests --one-function-checks` prints each module that calls a SETUP_CALLS name, then the counts,
and exits non-zero when the list differs from `one_function_leftovers.txt`. Only a module declared SMOKE (file name ends
`_smoke`, or the docstring opens `SMOKE`) may build a game. The list may only shrink: a module not in it fails, and a
listed module that no longer calls one fails too.

This reads the syntax tree and runs nothing. A module that defines its own function of a setup name, or takes one as a
parameter, is not charged for calls to it. A module whose function under test is itself a command (`commission_mines`,
`open_mine`) names it in a module-level `UNDER_TEST = {"commission_mines"}`, and calls to the names it lists are not
charged; a game or economy builder can never be listed.
"""
import ast
import os

from sim.tests.discovery import TESTS_DIR, discover_topics

# Building a game or an economy, or running it: each stands for many functions at once.
GAME_AND_ECONOMY_BUILDERS = {"sim", "unopened_sim", "build_unopened", "Sim", "proto", "Economy", "blank_economy",
                             "years_of", "spin_up", "spin_up_trace"}
# Commands that change a game's state: a test that needs their result builds that result instead.
# A unit's own `step` (a population's, a store's) is a function under test like any other; stepping a game or an
# economy needs one built first, and the builders above are what is flagged.
STATE_COMMANDS = {"hire", "open_venture", "run_it", "start_project", "open_mine", "open_plant", "open_agent",
                  "advance_actors", "founder_runs", "founder_completes", "commission_mines"}
SETUP_CALLS = GAME_AND_ECONOMY_BUILDERS | STATE_COMMANDS
FIXTURE_MODULES = {"fixture", "economy_fixture", "cli_in_process"}   # their `run` plays years or the CLI
SMOKE_SUFFIX = "_smoke"
SMOKE_OPENING = "SMOKE"
PREFILTER = tuple(sorted({name + "(" for name in SETUP_CALLS} | {".run("}))   # parse only files that might call one
LEFTOVERS_PATH = os.path.join(TESTS_DIR, "one_function_leftovers.txt")


def is_smoke(topic, source=""):
    """True when the topic's name or its docstring's opening declares it a smoke test of the whole game."""
    if topic.endswith(SMOKE_SUFFIX):
        return True
    docstring = ast.get_docstring(ast.parse(source)) or ""
    return docstring.lstrip().startswith(SMOKE_OPENING)


def declared_under_test(tree):
    """The names a module's top-level `UNDER_TEST = {...}` lists (a set, list or tuple of strings), else none."""
    for node in tree.body:
        if (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "UNDER_TEST"
                                                  for target in node.targets)
                and isinstance(node.value, (ast.Set, ast.List, ast.Tuple))):
            return {element.value for element in node.value.elts
                    if isinstance(element, ast.Constant) and isinstance(element.value, str)}
    return set()


def setup_calls(source, path="<source>"):
    """[(line, name)] for each call in the source to a game or economy builder or a state command."""
    tree = ast.parse(source, filename=path)
    own_definitions = {node.name for node in ast.walk(tree)
                       if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in SETUP_CALLS}
    parameters = {argument.arg for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.Lambda))
                  for argument in node.args.args + node.args.kwonlyargs}
    under_test = declared_under_test(tree) & STATE_COMMANDS
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Name):
            if (function.id in SETUP_CALLS and function.id not in own_definitions and function.id not in parameters
                    and function.id not in under_test):
                found.append((node.lineno, function.id))
        elif isinstance(function, ast.Attribute):
            owner = function.value.id if isinstance(function.value, ast.Name) else None
            if function.attr == "run" and owner in FIXTURE_MODULES:
                found.append((node.lineno, "%s.run" % owner))
            elif function.attr in SETUP_CALLS and function.attr not in own_definitions and function.attr not in under_test:
                found.append((node.lineno, "%s.%s" % (owner or "...", function.attr)))
    return sorted(found)


def offending_modules(tests_dir=TESTS_DIR):
    """{topic: (first setup call as (line, name), how many)} for each module that is not a smoke test."""
    found = {}
    for topic in discover_topics(tests_dir):
        path = os.path.join(tests_dir, "test_%s.py" % topic)
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        if not any(token in source for token in PREFILTER) or is_smoke(topic, source):
            continue
        calls = setup_calls(source, path)
        if calls:
            found[topic] = (calls[0], len(calls))
    return found


def listed_leftovers(path=LEFTOVERS_PATH):
    """Topics named in the leftovers file (one per line; `#` starts a comment)."""
    with open(path, encoding="utf-8") as handle:
        lines = [line.split("#")[0].strip() for line in handle]
    return {line for line in lines if line}


def differences(found, listed):
    """(new, stale): offending modules the list lacks, and listed topics that no longer offend."""
    return sorted(set(found) - set(listed)), sorted(set(listed) - set(found))


def report():
    found = offending_modules()
    new, stale = differences(found, listed_leftovers())
    for topic in sorted(found):
        (line, name), count = found[topic]
        print("%-8s %s:%d  %s  (%d setup calls)" % ("NEW" if topic in new else "listed", topic, line, name, count))
    for topic in stale:
        print("STALE    %s (gone, a smoke test, or calls only its function: remove it from one_function_leftovers.txt)"
              % topic)
    print("\nmodules that reach their function through other engine functions: %d (%d not in the leftovers list, "
          "%d stale list entries)" % (len(found), len(new), len(stale)))
    return len(new) + len(stale)
