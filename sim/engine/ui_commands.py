"""Player commands and automatic policies declared as data (data/ui/commands.json of each mod).

A declaration is one of three kinds:
  read    a table of values read from state paths (same path grammar and @readable gate as figures)
  macro   a fixed list of existing commands run in order, with `$name` standing for a field of the typed command
  policy  when every condition on state paths holds at a yearly hook, run a list of existing commands
This module checks the shape and the state paths; the command registry (sim/ui) checks the commands named.
A name is `<mod_id>:<name>`, except that an entry may carry `"override": true` or `"remove": true` to change or
delete a command that already exists.
"""
import os
from typing import Any, Dict, List, NamedTuple, Optional

from sim.json_files import read_json

from .mods import get_ordered_mods
from .mods_base import ModError, claim_fields
from .mods_ids import check_new_id
from .tree_source import ROOT
from .ui_data import check_state_path

COMMANDS_FILE = os.path.join("data", "ui", "commands.json")
KINDS = ("read", "macro", "policy")
HOOKS = ("year_start", "year_end")
SHAPES = ("bare", "text", "tech")
OPERATORS = (">=", "<=", ">", "<", "==", "!=")
DOCUMENTATION_FIELDS = ("group", "summary", "usage", "options", "description", "aliases")


class CommandSpec(NamedTuple):
    mod_id: str
    path: str
    name: str
    spec: Dict[str, Any]


def _check_steps(steps: Any, where: str) -> None:
    if not isinstance(steps, list) or not steps:
        raise ModError("%s needs a non-empty list of command objects" % where)
    for step in steps:
        if not isinstance(step, dict) or not isinstance(step.get("cmd"), str):
            raise ModError("%s: every step must be an object with a string 'cmd'" % where)


def _check_new(name: str, spec: Dict[str, Any], path: str) -> None:
    where = "%s: command %s" % (path, name)
    if spec.get("kind") not in KINDS:
        raise ModError("%s needs 'kind' to be one of %s" % (where, ", ".join(KINDS)))
    for field in ("summary", "description"):
        if not isinstance(spec.get(field), str):
            raise ModError("%s needs a string %r" % (where, field))
    if spec.get("kind") == "policy":
        hook = spec.get("hook")
        if hook not in HOOKS:
            raise ModError("%s needs 'hook' to be one of %s" % (where, ", ".join(HOOKS)))
        for condition in spec.get("when") or []:
            if condition.get("op") not in OPERATORS or not isinstance(condition.get("path"), str):
                raise ModError("%s: a condition needs a state 'path' and an 'op' of %s" % (where, ", ".join(OPERATORS)))
            check_state_path(condition["path"], where)
        _check_steps(spec.get("do"), where + " 'do'")
        return
    if spec.get("shape", "bare") not in SHAPES:
        raise ModError("%s: 'shape' must be one of %s" % (where, ", ".join(SHAPES)))
    if spec["kind"] == "read":
        shows = spec.get("shows")
        if not isinstance(shows, list) or not shows:
            raise ModError("%s needs 'shows', a list of {label, path}" % where)
        for row in shows:
            if not isinstance(row.get("label"), str) or not isinstance(row.get("path"), str):
                raise ModError("%s: every 'shows' row needs a string label and path" % where)
            check_state_path(row["path"], where)
    else:
        _check_steps(spec.get("steps"), where + " 'steps'")


def load_command_specs(root: str = ROOT, mods_dir: Optional[str] = None) -> List[CommandSpec]:
    """Every mod's command declarations in load order, checked for shape and state paths."""
    mods_dir = mods_dir or os.path.join(root, "mods")
    found: List[CommandSpec] = []
    for manifest in get_ordered_mods(mods_dir):
        path = os.path.join(manifest.directory, COMMANDS_FILE)
        if not os.path.isfile(path):
            continue
        for name, spec in (read_json(path).get("commands") or {}).items():
            if not isinstance(spec, dict):
                raise ModError("%s: command %s must be an object" % (path, name))
            if spec.get("remove") is True or spec.get("override") is True:
                bad = [key for key in spec if key not in DOCUMENTATION_FIELDS + ("override", "remove")]
                if bad:
                    raise ModError("%s: command %s may only change %s, not %s" %
                                   (path, name, ", ".join(DOCUMENTATION_FIELDS), ", ".join(bad)))
            else:
                check_new_id(manifest, name, False, path)
                _check_new(name, spec, path)
            found.append(CommandSpec(manifest.id, path, name, spec))
    return found


POLICIES_FILE = os.path.join("data", "ui", "policies.json")


def policy_defaults(manual: bool, root: str = ROOT, mods_dir: Optional[str] = None) -> Dict[str, Any]:
    """Switches mods add to a new seat's policy, and shipped switches whose default a mod sets.

    A mod policy declared in commands.json becomes a switch named `<mod_id>:<name>`, on unless its `default` says
    otherwise (off for a player who plays by hand when `default` is absent). `data/ui/policies.json` of a mod,
    `{"defaults": {"auto_mine": false}}`, sets the shipped default of an existing switch; two unrelated mods
    setting the same switch is an error naming both."""
    mods_dir = mods_dir or os.path.join(root, "mods")
    switches: Dict[str, Any] = {}
    for found in load_command_specs(root, mods_dir):
        if found.spec.get("kind") == "policy" and "remove" not in found.spec:
            switches[found.name] = found.spec.get("default", not manual)
    manifests = get_ordered_mods(mods_dir)
    by_id = {manifest.id: manifest for manifest in manifests}
    claims: Dict[Any, str] = {}
    for manifest in manifests:
        path = os.path.join(manifest.directory, POLICIES_FILE)
        if not os.path.isfile(path):
            continue
        defaults = read_json(path).get("defaults") or {}
        if not all(isinstance(value, bool) for value in defaults.values()):
            raise ModError("%s: every default must be true or false" % path)
        claim_fields(claims, "policy default", "policies", defaults, manifest, by_id)
        switches.update({name: value for name, value in defaults.items()})
    return switches
