"""Complaint 574: each command takes the fields its own handler reads, not any field some command reads."""
import ast
import os

from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent, pristine_game
from sim.ui.proto import command_registry, field_check

game = pristine_game()

stray = ask_agent(game, cmd="policy", id="x")
check("policy given another command's field is refused as unknown",
      stray.get("ok") is False and getattr(stray.get("error"), "cause", None) == "unknown_field", stray)
check("...naming the field and the fields policy takes",
      stray.get("field") == "id" and stray.get("accepted_fields") == ["set"], stray)
check("why still takes id", getattr(ask_agent(game, cmd="why", id="x").get("error"), "cause", None) != "unknown_field")
check("another command's field is refused on a command that reads none",
      ask_agent(game, cmd="state", id="x").get("field") == "id")


def command_literals():
    """(file, line, command, fields) for each command written out in the tests: cmd="x", f=... or {"cmd": "x", ...}."""
    folder = os.path.dirname(__file__)
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".py") or name.startswith("test_unknown_field"):   # those write the refusals out
            continue
        with open(os.path.join(folder, name), encoding="utf-8") as source:
            tree = ast.parse(source.read())
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
for name, line, word, fields in command_literals():
    entry = command_registry.resolve(word) if isinstance(word, str) else None
    if entry is None:
        continue
    allowed = field_check.accepted_fields(entry) | common | {"as"}
    refused += ["%s:%d %s %s" % (name, line, word, field) for field in fields if field not in allowed]
check("every command literal in the tests passes the per-command field check", not refused, sorted(set(" ".join(item.split()[1:]) for item in refused)))
