"""Complaint 285: the player's chosen display units reach every covered screen.

A fake unit is registered per dimension (the stakeholder's `blob` for area),
selected, and every covered JSON reply and rendered screen is checked: every
quantity of the dimension carries the fake unit, none keeps another label, and
the number is the base value converted (so not equal to it). The same run is
repeated with a mod supplying the fake units. The default (nothing selected)
must leave every reply untouched.
"""
from .harness import *
import json as _json
import re as _re
import tempfile as _tempfile
from sim.engine import units as U
from sim.ui.proto.dispatch import _agent_dispatch
from sim.ui.proto.render_typed import render_pretty
from sim.ui.proto.util import _coin_hoard_line
from sim.ui.units_text import for_text

# Screens covered, by dimension: (render command name, command dict).
COVERED = {
    "area": [("buy", {"cmd": "buy", "what": "farm", "n": 5}),
             ("buy", {"cmd": "buy", "what": "forest", "n": 5})],
    "mass": [("materials", {"cmd": "materials"})],
    "money": [("state", {"cmd": "state"}), ("money", {"cmd": "money"}),
              ("buy", {"cmd": "buy", "what": "farm", "n": 5})],
}
# Mass quantities in tonnes: 14 t is 2 blob (7 kg each); the number printed is the converted one.
HAND_REPLIES = [
    ("why", {"ok": True, "id": "x", "name": "x", "material_rows": [
        {"material": "iron", "needed_tonnes": 14.0, "held_tonnes": 7.0,
         "missing_tonnes": 7.0, "cost_of_missing": 1.0}]}, "need 2,000"),
]
FAKE = {"area": "blob_area", "mass": "blob_mass", "money": "blob_money",
        "temperature": "blob_degree"}
FAKE_UNITS = {
    "blob_area": {"name": "blob", "symbol": "blob", "dimension": "area", "factor": 0.15},
    "blob_mass": {"name": "blob", "symbol": "blob", "dimension": "mass", "factor": 7.0},
    "blob_money": {"name": "blob", "symbol": "blob", "dimension": "money", "factor": 3.0},
    "blob_degree": {"name": "blob", "symbol": "blob", "dimension": "temperature",
                    "factor": 2.0, "offset": 10.0},
}
NATIVE_WORDS = {"area": r"\bhectares?\b|\bha\b", "mass": r"\btonnes?\b",
                "money": r"\bden\b|\bdenarii\b"}


def _fields(reply, dimension, registry, found=None):
    """Every (key, value, sibling display, rule) of a dimension in a reply tree."""
    found = [] if found is None else found
    if isinstance(reply, dict):
        for key, value in reply.items():
            if isinstance(value, (dict, list)):
                _fields(value, dimension, registry, found)
            elif (isinstance(value, (int, float)) and not isinstance(value, bool)
                  and not key.endswith("_display")):
                rule = U.field_rule(registry, key)
                if rule and rule["dimension"] == dimension:
                    found.append((key, value, reply.get(key + "_display"), rule))
    elif isinstance(reply, list):
        for item in reply:
            _fields(item, dimension, registry, found)
    return found


def _run(registry, label, fake_ids, fake_specs):
    U.set_registry(registry)
    for dimension, screens in COVERED.items():
        spec = fake_specs[fake_ids[dimension]]
        U.set_preferences({dimension: fake_ids[dimension]})
        for command_name, command in screens:
            game = sim(capital=5_000_000.0)
            reply = _agent_dispatch(game, NODES, dict(command))
            found = _fields(reply, dimension, registry)
            screen = "%s: %s %s %s" % (label, command["cmd"], command.get("what", ""), dimension)
            check(screen + " has fields", len(found) > 0, reply)
            for key, value, shown, rule in found:
                labelled = (isinstance(shown, dict) and shown.get("unit") == "blob"
                            and shown.get("symbol") == "blob")
                check("%s.%s labelled blob" % (screen, key), labelled, shown)
                if not labelled or not value:
                    continue
                base = value * U.native_factor(registry, rule, game)
                expected = (base - spec.get("offset", 0.0)) / spec["factor"]
                check("%s.%s converted" % (screen, key),
                      abs(shown["value"] - expected) <= 0.011 * max(1.0, abs(expected))
                      and shown["value"] != value, (value, shown, expected))
            text = render_pretty(command_name, reply)
            check(screen + " text uses blob", "blob" in text, text)
            if (command_name, dimension) != ("buy", "money"):
                # Command syntax lines name the unit a command accepts; not a quantity.
                shown_lines = [line for line in text.splitlines() if "<" not in line]
                leaked = _re.findall(NATIVE_WORDS[dimension], "\n".join(shown_lines))
                check(screen + " text keeps no native label", not leaked, (leaked, text))
    # Hand-written replies for screens that print their own mass labels.
    U.set_preferences({"mass": fake_ids["mass"]})
    for name, reply, expect in HAND_REPLIES:
        shown = U.add_display(_json.loads(_json.dumps(reply)), None)
        text = render_pretty(name, shown)
        screen = "%s: hand-written %s" % (label, name)
        leaked = _re.findall(NATIVE_WORDS["mass"], text)
        check(screen + " keeps no tonne label", not leaked, (leaked, text))
        check(screen + " says blob", "blob" in text, text)
        check(screen + " number converted", expect in text, (expect, text))
    hoard = U.add_display({"coin_hoard": {"metal": "silver_kg", "tonnes": 14.0,
                                          "keeping_cost_per_year": 1.0}}, None)
    hoard_text = "\n".join(_coin_hoard_line(for_text(hoard, False)))
    check(label + ": coin hoard line labelled blob", "2000 blob of silver" in hoard_text
          or "2,000 blob of silver" in hoard_text, hoard_text)
    # Temperature has no screen in the game yet: the formatter and field rule
    # are exercised on a synthetic reply (see Complaint 285's remains).
    U.set_preferences({"temperature": fake_ids["temperature"]})
    synthetic = U.add_display({"ok": True, "furnace_celsius": 100.0}, None)
    shown = synthetic.get("furnace_celsius_display") or {}
    check("%s: temperature field labelled blob and converted" % label,
          shown.get("unit") == "blob" and abs(shown.get("value", 0) - 45.0) < 0.01, synthetic)
    U.set_preferences({})


# Registry as shipped, plus the fake units appended in memory.
_with_fakes = _json.loads(_json.dumps(U.load_units(ROOT)))
_with_fakes["units"].update(FAKE_UNITS)
_run(_with_fakes, "in-memory", FAKE, FAKE_UNITS)

# Default preference leaves every covered reply untouched.
U.set_registry(_with_fakes)
U.set_preferences({})
_default = _agent_dispatch(sim(capital=5_000_000.0), NODES, {"cmd": "state"})
check("default adds no _display fields", "_display" not in _json.dumps(_default))

# The same, with a real mod directory supplying the fake units.
with _tempfile.TemporaryDirectory() as _tmp:
    _mod = os.path.join(_tmp, "mods", "test_blobs_k3f9")
    os.makedirs(os.path.join(_mod, "data", "world"))
    with open(os.path.join(_mod, "mod.json"), "w") as _handle:
        _json.dump({"id": "test_blobs_k3f9", "name": "Blobs", "version": "1",
                    "dependencies": [], "conflicts": []}, _handle)
    _mod_ids = {dimension: "test_blobs_k3f9:" + name[len("blob_"):] for dimension, name in FAKE.items()}
    _mod_specs = {"test_blobs_k3f9:" + name[len("blob_"):]: dict(spec) for name, spec in FAKE_UNITS.items()}
    with open(os.path.join(_mod, "data", "world", "units.json"), "w") as _handle:
        _json.dump({"units": _mod_specs}, _handle)
    _run(U.load_units(ROOT, os.path.join(_tmp, "mods")), "mod", _mod_ids, _mod_specs)
    # A mod unit not namespaced to the mod is refused.
    with open(os.path.join(_mod, "data", "world", "units.json"), "w") as _handle:
        _json.dump({"units": {"stray": dict(FAKE_UNITS["blob_area"])}}, _handle)
    try:
        U.load_units(ROOT, os.path.join(_tmp, "mods"))
        check("unnamespaced mod unit refused", False)
    except Exception as _error:
        check("unnamespaced mod unit refused", "stray" in str(_error), _error)
U.set_registry(None)
U.set_preferences({})
