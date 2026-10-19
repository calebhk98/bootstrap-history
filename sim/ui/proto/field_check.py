"""Refuse a command field that nothing reads, instead of replying `ok` to a request that did nothing.

The fields a command may carry are found, not listed: every field the handlers read off the command
(`cmd.get("x")`, `cmd["x"]`, `"x" in cmd`), plus the fields in each command's declared JSON usage forms.
"""
import ast
import inspect
import json
import os

from sim.refusal import Refusal
from . import command_registry

RECEIVER_NAMES = ("cmd", "command", "request", "args", "params", "spec", "body")
_read_cache = {}


def _fields_read_in(path):
    """Fields one source file reads off a command-like variable."""
    if path in _read_cache:
        return _read_cache[path]
    fields = set()
    try:
        with open(path, encoding="utf-8") as source:
            tree = ast.parse(source.read())
    except (OSError, SyntaxError):
        tree = ast.parse("")
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and any(isinstance(arg, ast.Name) and arg.id in RECEIVER_NAMES for arg in node.args)):
            # a helper handed the command and the field's name: read_quantity(cmd, "amount", ...)
            fields.update(arg.value for arg in node.args
                          if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.isidentifier())
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("get", "pop", "setdefault")
                and isinstance(node.func.value, ast.Name) and node.func.value.id in RECEIVER_NAMES
                and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            fields.add(node.args[0].value)
        elif (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
              and node.value.id in RECEIVER_NAMES
              and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str)):
            fields.add(node.slice.value)
        elif (isinstance(node, ast.Compare) and len(node.comparators) == 1
              and isinstance(node.comparators[0], ast.Name) and node.comparators[0].id in RECEIVER_NAMES
              and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)):
            fields.add(node.left.value)
    _read_cache[path] = fields
    return fields


def _module_paths():
    paths = set()
    for folder in (os.path.dirname(__file__), os.path.dirname(os.path.dirname(__file__))):
        paths.update(os.path.join(folder, name) for name in os.listdir(folder) if name.endswith(".py"))
    for entry in command_registry.COMMANDS.values():
        if entry["handler"] is not None:
            paths.add(inspect.getsourcefile(entry["handler"]) or "")
    return paths


def declared_fields(entry):
    """The fields a command's JSON usage forms carry, other than `cmd`."""
    fields = set()
    for form in entry["usage"]:
        if not form.lstrip().startswith("{"):
            continue
        try:
            parsed = json.loads(form)
        except ValueError:
            continue
        if isinstance(parsed, dict):
            fields.update(parsed)
    fields.discard("cmd")
    return fields


def known_fields():
    """Every field some handler reads or some command declares."""
    fields = {"cmd"}
    for path in _module_paths():
        fields |= _fields_read_in(path)
    for entry in command_registry.COMMANDS.values():
        fields |= declared_fields(entry)
    return fields


def unknown_field_refusal(cmd):
    """A refusal naming the first field no command reads, or None."""
    entry = command_registry.resolve(cmd.get("cmd") if isinstance(cmd.get("cmd"), str) else "")
    if entry is None:
        return None
    known = known_fields()
    stray = sorted(field for field in cmd if field not in known)
    if not stray:
        return None
    accepted = sorted(declared_fields(entry))
    if not accepted and entry["handler"] is not None:
        accepted = sorted(_fields_read_in(inspect.getsourcefile(entry["handler"]) or "") - {"cmd"})
    return {"ok": False,
            "error": Refusal("unknown_field",
                             "%s does not take a field called %r; nothing was changed.%s"
                             % (entry["name"], stray[0],
                                " Fields it takes: %s." % ", ".join(accepted) if accepted else ""),
                             choices=accepted, field=stray[0]),
            "field": stray[0], "accepted_fields": accepted}
