"""Refuse a command field its own command does not read, instead of replying `ok` to a request that did nothing.

The fields a command may carry are found, not listed: the fields its handler reads off the command (`cmd.get("x")`,
`cmd["x"]`, `"x" in cmd`, following the command into the helpers it is handed to), the fields in its declared JSON
usage forms, and the few fields every command carries (the seat it acts as, the compact flag).
"""
import ast
import inspect
import json
import textwrap

from sim.refusal import Refusal
from . import command_registry

RECEIVER_NAMES = ("cmd", "command", "request", "args", "params", "spec", "body")


def _string(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _is_receiver(node, receivers):
    """The command itself, or `(cmd or {})`."""
    if isinstance(node, ast.BoolOp):
        return any(_is_receiver(value, receivers) for value in node.values)
    return isinstance(node, ast.Name) and node.id in receivers


def _callee(call, scope):
    """The function a call names, looked up in the module `scope` (a globals dict), or None."""
    func = call.func
    if isinstance(func, ast.Name):
        target = scope.get(func.id)
    elif (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
          and inspect.ismodule(scope.get(func.value.id))):
        target = getattr(scope[func.value.id], func.attr, None)
    else:
        return None
    return target if inspect.isfunction(target) else None


def fields_read_by(function, receivers=RECEIVER_NAMES, seen=None, follow=True):
    """Fields `function` reads off the command, including those read by helpers it hands the command to."""
    seen = set() if seen is None else seen
    key = (function, tuple(sorted(receivers)))
    if key in seen:
        return set()
    seen.add(key)
    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    except (OSError, TypeError, SyntaxError):
        return set()
    scope = getattr(function, "__globals__", {})
    fields = set()
    dynamic = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and follow:
            # a sibling function, or a table of them: {"material": _buy_material}
            target = scope.get(node.id)
            targets = list(target.values()) if isinstance(target, dict) else [target]
            for each in targets:
                if (inspect.isfunction(each) and each.__module__.startswith("sim.ui.proto")
                        and each is not function):
                    fields |= fields_read_by(each, receivers, seen)
        if isinstance(node, ast.Call):
            positions = [index for index, arg in enumerate(node.args)
                         if isinstance(arg, ast.Name) and arg.id in receivers]
            if positions:
                # a helper handed the command and the field's name: read_quantity(cmd, "amount", ...)
                fields.update(text for text in map(_string, node.args) if text and text.isidentifier())
                callee = _callee(node, scope)
                if callee is not None and follow:
                    names = list(inspect.signature(callee).parameters)
                    handed = {names[index] for index in positions if index < len(names)}
                    fields |= fields_read_by(callee, tuple(set(receivers) | handed), seen)
            if (isinstance(node.func, ast.Attribute) and node.func.attr in ("get", "pop", "setdefault")
                    and _is_receiver(node.func.value, receivers)
                    and node.args):
                if _string(node.args[0]):
                    fields.add(_string(node.args[0]))
                else:
                    dynamic = True
        elif (isinstance(node, ast.Subscript) and _is_receiver(node.value, receivers)):
            if _string(node.slice):
                fields.add(_string(node.slice))
            else:
                dynamic = True
        elif (isinstance(node, ast.Compare) and len(node.comparators) == 1
              and isinstance(node.comparators[0], ast.Name) and node.comparators[0].id in receivers
              and _string(node.left)):
            fields.add(_string(node.left))
    if dynamic:
        fields |= _listed_names(tree, scope)
    return fields


def _listed_names(tree, scope):
    """Names in the tuples a function loops over to read fields by variable: literal ones and module constants."""
    names = set()
    for node in ast.walk(tree):
        value = None
        if isinstance(node, (ast.Tuple, ast.List)):
            value = [_string(element) for element in node.elts]
        elif isinstance(node, ast.Name) and isinstance(scope.get(node.id), (tuple, list, frozenset, set)):
            value = list(scope[node.id])
        if value:
            names.update(text for text in value if isinstance(text, str) and text.isidentifier())
    return names


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


def common_fields():
    """Fields every command carries: those the reply wrapper reads and the output switches the typed parser sets."""
    from . import dispatch, typed
    return fields_read_by(dispatch._agent_reply, follow=False) | set(typed._JSON_WORDS) | {"cmd"}


def accepted_fields(entry):
    """Every field this command takes beyond the common ones: what its handler reads and its declared forms."""
    fields = declared_fields(entry)
    if entry["handler"] is not None:
        fields |= fields_read_by(entry["handler"])
    if entry["shape"] in ("tech", "tech_done"):
        fields.add("id")   # a typed name is resolved onto `id` before the handler runs
    return fields


def _unreadable(handler):
    """A lambda has no source of its own, and a mod's handler takes the fields its data declares."""
    return handler is not None and (handler.__name__ == "<lambda>" or handler.__module__.endswith(".mod_commands"))


def unknown_field_refusal(cmd, table=command_registry.SHIPPED):
    """A refusal naming the first field the command does not take, or None."""
    entry = table.resolve(cmd.get("cmd") if isinstance(cmd.get("cmd"), str) else "")
    if entry is None or _unreadable(entry["handler"]):
        return None
    common = common_fields()
    own = accepted_fields(entry)
    stray = sorted(field for field in cmd if field not in own and field not in common)
    if not stray:
        return None
    accepted = sorted(own - common)
    return {"ok": False,
            "error": Refusal("unknown_field",
                             "%s does not take a field called %r; nothing was changed.%s"
                             % (entry["name"], stray[0],
                                " Fields it takes: %s." % ", ".join(accepted) if accepted else ""),
                             choices=accepted, field=stray[0]),
            "field": stray[0], "accepted_fields": accepted}
