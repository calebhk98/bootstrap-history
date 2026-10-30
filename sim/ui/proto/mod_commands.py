"""What a mod's data commands do when run, and its automatic policies.

Which commands a game has (the shipped ones, the mods' data and code, their patches) is the interface module's; this module is
the code behind a data declaration: a `read` table of state paths, a `macro` replaying existing commands through the ordinary
dispatcher (so fog guards, option checks and money localisation apply), and the policies a year hook runs.
"""
import operator

from . import command_registry

_OPERATORS = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt,
              "==": operator.eq, "!=": operator.ne}


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


def data_command_handler(kind, name, spec):
    """The handler of a command declared as data (`read` or `macro`)."""
    return _reader(name, spec) if kind == "read" else _macro(spec)


def _holds(sim, condition):
    return _OPERATORS[condition["op"]](_read_path(sim, condition["path"]), condition["value"])


def run_policies(sim, nodes, hook):
    """Run every switched-on data policy of this hook whose conditions hold; the lines to add to the year's log."""
    lines = []
    for name, spec in command_registry.table_of(sim).policies:
        if spec["hook"] != hook or not sim.view("founder")()["policy"].get(name, False):
            continue
        if not all(_holds(sim, condition) for condition in spec.get("when") or ()):
            continue
        outcome = _run_steps(sim, nodes, spec["do"], {})
        lines.append("%s: %s" % (name, "ran %d command(s)" % len(outcome["steps"]) if outcome["ok"]
                                  else outcome["error"]))
    return lines
