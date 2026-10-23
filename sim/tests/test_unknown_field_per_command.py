"""Complaint 574: each command takes the fields its own handler reads, not any field some command reads. The refusal rule is
called on built commands in test_field_check_rule; this lint holds the command literals the tests write out to it."""
QUICK_TOPIC = True

import ast
import os

from .harness import check
from sim.ui.proto import command_registry, field_check


def command_literals():
    """(file, line, command, fields) for each command written out in the tests: cmd="x", f=... or {"cmd": "x", ...}."""
    folder = os.path.dirname(__file__)
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".py") or name.startswith(("test_unknown_field", "test_field_check_rule")):   # those write the refusals out
            continue
        with open(os.path.join(folder, name), encoding="utf-8") as source:
            text = source.read()
        if "cmd" not in text:
            continue
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                named = {keyword.arg: keyword.value for keyword in node.keywords}
                if "cmd" in named and None not in named and isinstance(named["cmd"], ast.Constant):
                    yield name, node.lineno, named["cmd"].value, [field for field in named if field != "cmd"]
            elif isinstance(node, ast.Dict) and None not in node.keys:
                items = {key.value: value for key, value in zip(node.keys, node.values)
                         if isinstance(key, ast.Constant) and isinstance(key.value, str)}
                if len(items) == len(node.keys) and isinstance(items.get("cmd"), ast.Constant):
                    yield name, node.lineno, items["cmd"].value, [field for field in items if field != "cmd"]


refused = []
common = field_check.common_fields()
allowed_by_command = {}   # the handler's fields are read from its source once per command
for name, line, word, fields in command_literals():
    entry = command_registry.resolve(word) if isinstance(word, str) else None
    if entry is None:
        continue
    if word not in allowed_by_command:
        allowed_by_command[word] = field_check.accepted_fields(entry) | common | {"as"}
    allowed = allowed_by_command[word]
    refused += ["%s:%d %s %s" % (name, line, word, field) for field in fields if field not in allowed]
check("every command literal in the tests passes the per-command field check", not refused, sorted(set(" ".join(item.split()[1:]) for item in refused)))
