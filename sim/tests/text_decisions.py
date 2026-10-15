"""Lists the places in sim/ (not tests) that decide by reading a log line's or a refusal's text (Complaint 521).

`python3 -m sim.tests --text-decisions` prints one line per decision and the count; the complaint closes when that
list is empty. A decision on a log line's or refusal's text breaks when the wording changes, and silently stops
working for a line the save once turned into plain text. The code reads the line's `kind` (or a refusal's `cause`)
and its `facts` instead (sim/refusal.py).

This reads the syntax tree and runs nothing, so it is a heuristic, in the spirit of text_checks.py. A name holds
line text when it is a loop target over a log (`for year, message in sim.log`), a parameter called `message` or `msg`, or a
read of a reply's `message` or `error` key. A decision is a comparison (`in`, `==`), a `startswith`-style
method call or a `re` call whose operand is such text. Code whose subject is presentation (a renderer, fog
redaction) says so with `# presentation: <reason>` on the line or the line above, as in text_checks.py; files named
`render*` are presentation as a whole.
"""
import ast
import os
import re

from sim.tests.text_checks import PRESENTATION_MARK

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT_KEYS = ("message", "error")
WRAPPERS = ("lower", "upper", "strip", "casefold")
DECIDING_METHODS = ("startswith", "endswith", "find", "index", "count", "partition", "split")
REGEX_CALLS = ("search", "match", "findall", "fullmatch", "sub", "finditer")


def _reads_log(node, logs):
    """Whether an expression is a log: `.log`, a slice or copy of one, or a name already known to hold one."""
    while True:
        if isinstance(node, ast.Subscript):
            node = node.value
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.args and node.func.id in (
                "list", "sorted", "reversed", "tuple"):
            node = node.args[0]
        else:
            break
    if isinstance(node, ast.Attribute):
        return node.attr == "log"
    return isinstance(node, ast.Name) and (node.id == "log" or node.id in logs)


def _target_names(target):
    return [part.id for part in ast.walk(target) if isinstance(part, ast.Name)]


def _log_names(tree):
    """Names assigned directly from a log."""
    names = set()
    for _round in range(3):
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                    and _reads_log(node.value, names):
                names.add(node.targets[0].id)
    return names


def _text_names(tree):
    """Names bound to a log line's text: the last target of a loop over a log."""
    logs = _log_names(tree)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.comprehension)) and _reads_log(node.iter, logs):
            last = node.target.elts[-1] if isinstance(node.target, ast.Tuple) else node.target
            names.update(_target_names(last))
    for node in ast.walk(tree):   # a parameter called message or msg
        if isinstance(node, ast.arg) and node.arg in ("message", "msg"):
            names.add(node.arg)
    for _round in range(3):   # a name assigned from text (`lowered = event["message"].lower()`) is text
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                    and _is_text(node.value, names):
                names.add(node.targets[0].id)
    return names


def _is_text(node, names):
    """Whether an expression is a log line's or refusal's text."""
    while isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in WRAPPERS:
        node = node.func.value
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "str" and node.args:
        return _is_text(node.args[0], names)
    if isinstance(node, ast.Name):
        return node.id in names
    if isinstance(node, ast.Subscript):
        key = node.slice
        return isinstance(key, ast.Constant) and key.value in TEXT_KEYS
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args:
        key = node.args[0]
        return isinstance(key, ast.Constant) and key.value in TEXT_KEYS
    return False


def _is_literal_text(node):
    return any(isinstance(part, ast.Constant) and isinstance(part.value, str) for part in ast.walk(node))


def _marked(lines, lineno):
    return any(PRESENTATION_MARK in lines[index] for index in (lineno - 1, lineno - 2) if 0 <= index < len(lines))


def scan_source(text, path="<source>"):
    """[(path, line, source)] for each decision on a log line's or refusal's text in one source file."""
    tree = ast.parse(text)
    lines = text.split("\n")
    names = _text_names(tree)
    found = []
    for node in ast.walk(tree):
        decided = False
        if isinstance(node, ast.Compare):
            operands = [node.left] + list(node.comparators)
            decided = (any(isinstance(op, (ast.In, ast.NotIn, ast.Eq, ast.NotEq)) for op in node.ops)
                       and any(_is_text(operand, names) for operand in operands)
                       and not any(isinstance(operand, ast.Constant) and operand.value is None for operand in operands))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in DECIDING_METHODS and _is_text(node.func.value, names):
                decided = True
            elif node.func.attr in REGEX_CALLS and isinstance(node.func.value, ast.Name) and node.func.value.id == "re":
                decided = any(_is_text(argument, names) for argument in node.args[1:])
        if decided and not _marked(lines, node.lineno):
            found.append((path, node.lineno, ast.get_source_segment(text, node) or ""))
    return found


def sources():
    """Every .py file under sim/ outside the tests and the renderers."""
    for directory, directory_names, file_names in os.walk(ROOT):
        directory_names[:] = [name for name in directory_names if name not in ("tests", "__pycache__")]
        for file_name in sorted(file_names):
            if file_name.endswith(".py") and not file_name.startswith("render"):
                yield os.path.join(directory, file_name)


def scan():
    """Every decision on a log line's or refusal's text under sim/ (the repository-relative path, line, source)."""
    found = []
    for path in sources():
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        try:
            found.extend(scan_source(text, os.path.relpath(path, os.path.dirname(ROOT))))
        except SyntaxError:
            continue
    return found


def report():
    """Prints the decisions and the count; returns how many there are."""
    found = scan()
    for path, lineno, source in found:
        print("%s:%d  %s" % (path, lineno, " ".join(source.split())[:110]))
    print("%d decisions on a log line's or refusal's text" % len(found))
    return len(found)


if __name__ == "__main__":
    raise SystemExit(1 if report() else 0)
