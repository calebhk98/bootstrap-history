"""SCENARIO (Complaint 640): Complaint 640, audit batch 3, scenario (complaint 285): the player's chosen display units reach every covered screen of
a played game, in the replies and in the rendered text, with the fake units supplied in memory and by a mod. The
conversion itself is tested on built replies in test_complaint_285_display_units."""
import json as _json
import re as _re
import tempfile as _tempfile

from .harness import *
from sim.engine import units as U
from sim.ui.proto.dispatch import _agent_dispatch
from sim.ui.proto.render_typed import render_pretty

# Screens covered, by dimension: (render command name, command dict).
COVERED = {
    "area": [("buy", {"cmd": "buy", "what": "farm", "n": 5}),
             ("buy", {"cmd": "buy", "what": "forest", "n": 5})],
    "mass": [("materials", {"cmd": "materials"})],
    "money": [("state", {"cmd": "state"}), ("money", {"cmd": "money"}),
              ("buy", {"cmd": "buy", "what": "farm", "n": 5})],
}
FAKE = {"area": "blob_area", "mass": "blob_mass", "money": "blob_money"}
FAKE_UNITS = {
    "blob_area": {"name": "blob", "symbol": "blob", "dimension": "area", "factor": 0.15},
    "blob_mass": {"name": "blob", "symbol": "blob", "dimension": "mass", "factor": 7.0},
    "blob_money": {"name": "blob", "symbol": "blob", "dimension": "money", "factor": 3.0},
}
NATIVE_WORDS = {"area": r"\bhectares?\b|\bha\b", "mass": r"\btonnes?\b", "money": r"\bden\b|\bdenarii\b"}

# One game serves every screen: the replies are read for their unit fields and the buys only move prices and cash.
_GAME = sim(capital=5_000_000.0)


def _fields(reply, dimension, registry, found=None):
    """Every (key, value, sibling display, rule) of a dimension in a reply tree."""
    found = [] if found is None else found
    if isinstance(reply, dict):
        for key, value in reply.items():
            if isinstance(value, (dict, list)):
                _fields(value, dimension, registry, found)
            elif (isinstance(value, (int, float)) and not isinstance(value, bool) and not key.endswith("_display")):
                rule = U.field_rule(registry, key)
                if rule and rule["dimension"] == dimension:
                    found.append((key, value, reply.get(key + "_display"), rule))
    elif isinstance(reply, list):
        for item in reply:
            _fields(item, dimension, registry, found)
    return found


def _run(registry, label, fake_ids, fake_specs):
    U.set_registry(registry)
    empty, unlabelled, unconverted, no_blob_text, native_left = [], [], [], [], []
    for dimension, screens in COVERED.items():
        spec = fake_specs[fake_ids[dimension]]
        U.set_preferences({dimension: fake_ids[dimension]})
        for command_name, command in screens:
            reply = _agent_dispatch(_GAME, NODES, dict(command))
            found = _fields(reply, dimension, registry)
            screen = "%s %s %s" % (command["cmd"], command.get("what", ""), dimension)
            if not found:
                empty.append(screen)
            for key, value, shown, rule in found:
                if not (isinstance(shown, dict) and shown.get("unit") == "blob" and shown.get("symbol") == "blob"):
                    unlabelled.append((screen, key, shown))
                    continue
                if not value:
                    continue
                expected = (value * U.native_factor(registry, rule, _GAME) - spec.get("offset", 0.0)) / spec["factor"]
                if not (abs(shown["value"] - expected) <= 0.011 * max(1.0, abs(expected)) and shown["value"] != value):
                    unconverted.append((screen, key, value, shown, expected))
            text = render_pretty(command_name, reply)
            if "blob" not in text:
                no_blob_text.append(screen)
            if (command_name, dimension) != ("buy", "money"):
                # Command syntax lines name the unit a command accepts; not a quantity.
                shown_lines = [line for line in text.splitlines() if "<" not in line]
                leaked = _re.findall(NATIVE_WORDS[dimension], "\n".join(shown_lines))
                if leaked:
                    native_left.append((screen, leaked))
    check(label + ": every covered screen has fields of its dimension", not empty, empty)
    check(label + ": every field of the dimension is labelled blob and its number is the base value converted",
          not unlabelled and not unconverted, (unlabelled[:3], unconverted[:3]))
    check(label + ": every covered screen's text uses blob and keeps no native label", not no_blob_text and not native_left,
          (no_blob_text, native_left))
    U.set_preferences({})


# Registry as shipped, plus the fake units appended in memory.
_with_fakes = _json.loads(_json.dumps(U.load_units(ROOT)))
_with_fakes["units"].update(FAKE_UNITS)
_run(_with_fakes, "scenario display units in memory", FAKE, FAKE_UNITS)

# Default preference leaves every covered reply untouched.
U.set_registry(_with_fakes)
U.set_preferences({})
check("scenario display units: the default adds no _display fields",
      "_display" not in _json.dumps(_agent_dispatch(_GAME, NODES, {"cmd": "state"})))

# The same, with a real mod directory supplying the fake units.
with _tempfile.TemporaryDirectory() as _tmp:
    _mod = os.path.join(_tmp, "mods", "test_blobs_k3f9")
    os.makedirs(os.path.join(_mod, "data", "world"))
    with open(os.path.join(_mod, "mod.json"), "w") as _handle:
        _json.dump({"id": "test_blobs_k3f9", "name": "Blobs", "version": "1", "dependencies": [], "conflicts": []}, _handle)
    _mod_ids = {dimension: "test_blobs_k3f9:" + name[len("blob_"):] for dimension, name in FAKE.items()}
    _mod_specs = {"test_blobs_k3f9:" + name[len("blob_"):]: dict(spec) for name, spec in FAKE_UNITS.items()}
    with open(os.path.join(_mod, "data", "world", "units.json"), "w") as _handle:
        _json.dump({"units": _mod_specs}, _handle)
    _run(U.load_units(ROOT, os.path.join(_tmp, "mods")), "scenario display units from a mod", _mod_ids, _mod_specs)
U.set_registry(None)
U.set_preferences({})
