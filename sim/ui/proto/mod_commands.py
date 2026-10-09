"""Commands and automatic policies that mods declare (data/ui/commands.json) or register from consented code.

`load_mod_commands()` runs once when the dispatcher loads, before the command tables are snapshotted. A mod command's
name is `<mod_id>:<name>`; an alias is a bare word that works only while no command, alias or mod claims it, and a
clash is an error naming both owners. Macros and policies replay existing commands through the ordinary dispatcher, so
fog guards, option checks and money localisation apply to them.
"""
import copy
import operator

import sim.engine.ui_port as ui_port

from . import command_registry
from .command_registry import COMMANDS, register_command, unregister

OWNERS = {}       # command name or alias word -> mod id ("" for the shipped game)
MOD_COMMANDS = {}  # name -> kind, for commands mods registered
POLICIES = []     # (name, spec) of data policies
_OPERATORS = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt,
              "==": operator.eq, "!=": operator.ne}
_REGISTERED_CODE = set()
_BACKUP = {}      # shipped command entries a mod changed or removed, as they were
_LOADED = []      # the mods directory already loaded


class ModCommandError(ValueError):
    """A mod's command cannot be registered."""


def _owner_of(word):
    return OWNERS.get(word, "the shipped game" if word in COMMANDS or word in command_registry.alias_map() else None)


def _claim(word, mod_id):
    holder = _owner_of(word)
    if holder is not None:
        raise ModCommandError("mod %s: the word %r is already taken by %s" % (mod_id, word, holder or "the shipped game"))
    OWNERS[word] = mod_id


def _read_path(sim, state_path):
    from sim.ui.figures_data import read_path
    return read_path(sim, state_path)


def _reader(name, spec):
    def handler(sim, nodes, cmd, ended):
        rows = []
        for row in spec["shows"]:
            value = _read_path(sim, row["path"])
            if isinstance(value, float) and "digits" in row:
                value = round(value, row["digits"])
            rows.append({"label": row["label"], "value": value, "unit": row.get("unit", "")})
        return {"ok": True, "command": name, "values": rows}
    return handler


def _fill(step, cmd):
    """The step with each `"$field"` string replaced by that field of the typed command, or the missing field's name."""
    built = {}
    for key, value in step.items():
        if isinstance(value, str) and value.startswith("$"):
            if value[1:] not in cmd:
                return None, value[1:]
            value = cmd[value[1:]]
        built[key] = value
    return built, None


def _run_steps(sim, nodes, steps, cmd):
    from .dispatch import _agent_dispatch_inner
    replies = []
    for position, step in enumerate(steps, 1):
        built, missing = _fill(step, cmd)
        if built is None:
            return {"ok": False, "error": "this command needs %r; nothing was run from step %d on" % (missing, position),
                    "steps": replies}
        reply = _agent_dispatch_inner(sim, nodes, built)
        replies.append(reply)
        if isinstance(reply, dict) and reply.get("ok") is False:
            return {"ok": False, "error": "step %d (%s) failed: %s" % (position, built["cmd"], reply.get("error", "refused")),
                    "steps": replies}
    return {"ok": True, "steps": replies}


def _macro(spec):
    def handler(sim, nodes, cmd, ended):
        return _run_steps(sim, nodes, spec["steps"], cmd)
    return handler


def _entry_fields(name, spec):
    return dict(group=spec.get("group", "mods"), summary=spec["summary"], usage=spec.get("usage", [name]),
                description=spec["description"], options=spec.get("options"), aliases=list(spec.get("aliases", ())),
                fog_hidden=bool(spec.get("fog_hidden", False)), shape=spec.get("shape", "bare"))


def _register(mod_id, name, fields, handler, kind):
    _claim(name, mod_id)
    for alias in fields.get("aliases", ()):
        _claim(alias, mod_id)
    register_command(name, handler=handler, **fields)
    MOD_COMMANDS[name] = kind


def _patch_documentation(found):
    name, spec = found.name, found.spec
    if name not in COMMANDS:
        raise ModCommandError("%s: mod %s changes missing command %r" % (found.path, found.mod_id, name))
    _BACKUP.setdefault(name, copy.deepcopy(COMMANDS[name]))
    if spec.get("remove") is True:
        for word in [name] + COMMANDS[name]["aliases"]:
            OWNERS.pop(word, None)
        unregister(name)
        return
    for field in ("group", "summary", "usage", "options", "description"):
        if field in spec:
            COMMANDS[name][field] = spec[field]
    for alias in spec.get("aliases", ()):
        _claim(alias, found.mod_id)
        COMMANDS[name]["aliases"].append(alias)


def _check_references():
    """Every command a macro or policy names must exist, and may not itself be a macro or a policy."""
    for name in [declared for declared in MOD_COMMANDS if declared in SPECS] + [policy for policy, _spec in POLICIES]:
        spec = SPECS[name]
        for step in spec.get("steps") or spec.get("do") or ():
            target = command_registry.resolve(step["cmd"])
            if target is None:
                raise ModCommandError("mod command %s names command %r, which does not exist (removed, or the "
                                      "mod's code is not allowed; see `simulator.py validate`)" % (name, step["cmd"]))
            if MOD_COMMANDS.get(target["name"]) == "macro":
                raise ModCommandError("mod command %s names the macro %s; a macro may not name a macro" %
                                      (name, target["name"]))


SPECS = {}


def load_mod_commands(mods_dir=None):
    """Register code commands, then data commands and policies, from every installed mod; safe to call again."""
    mods_dir = mods_dir or ui_port.MODDIR
    if _LOADED == [mods_dir]:
        return
    ui_port.run_mod_code(mods_dir)
    for registration in ui_port.COMMAND_REGISTRATIONS:
        if id(registration) in _REGISTERED_CODE:
            continue
        mod_id, name, fields, handler = registration
        _register(mod_id, name, dict(fields, aliases=list(fields.get("aliases", ()))), handler, "code")
        _REGISTERED_CODE.add(id(registration))
    for found in ui_port.load_command_specs(mods_dir=mods_dir):
        spec = found.spec
        if spec.get("override") is True or spec.get("remove") is True:
            _patch_documentation(found)
            continue
        SPECS[found.name] = spec
        if spec["kind"] == "policy":
            POLICIES.append((found.name, spec))
            continue
        handler = _reader(found.name, spec) if spec["kind"] == "read" else _macro(spec)
        _register(found.mod_id, found.name, _entry_fields(found.name, spec), handler, spec["kind"])
    _check_references()
    _LOADED[:] = [mods_dir]


def forget_mod_commands():
    """Drop everything mods registered and restore what they changed (for tests that install other mods)."""
    for name in list(MOD_COMMANDS):
        unregister(name)
    OWNERS.clear()
    for name, entry in _BACKUP.items():
        COMMANDS[name] = entry
    _BACKUP.clear()
    _LOADED.clear()
    MOD_COMMANDS.clear()
    POLICIES.clear()
    SPECS.clear()
    _REGISTERED_CODE.clear()


def _holds(sim, condition):
    return _OPERATORS[condition["op"]](_read_path(sim, condition["path"]), condition["value"])


def run_policies(sim, nodes, hook):
    """Run every switched-on data policy of this hook whose conditions hold; the lines to add to the year's log."""
    lines = []
    for name, spec in POLICIES:
        if spec["hook"] != hook or not sim.policy.get(name, False):
            continue
        if not all(_holds(sim, condition) for condition in spec.get("when") or ()):
            continue
        outcome = _run_steps(sim, nodes, spec["do"], {})
        lines.append("%s: %s" % (name, "ran %d command(s)" % len(outcome["steps"]) if outcome["ok"]
                                  else outcome["error"]))
    return lines
