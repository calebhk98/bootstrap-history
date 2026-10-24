"""The burndown of declared numbers cannot read zero while numbers are declared. Two bugs made `python3 sim/constants.py --burndown` print
"0 numbers declared": the import list named no module that calls declare(), and running the file as `__main__` loaded it a second time
under the name `sim.constants`, with a second registry that the report did not read. Each rule is called here on a registry built in the
test: `burndown` on a built registry, `declare` on the kinds, `_adopt_the_canonical_registry` on a stand-in canonical module, and
`_import_declaring_modules` with the import itself recorded rather than run."""

QUICK_TOPIC = True

import builtins
import collections
import json
import os
import subprocess
import sys
import types
from unittest import mock

from .harness import check

from sim import constants

REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def entry(name, kind):
    return {"name": name, "value": 1.0, "kind": kind, "unit": "u", "declared_in": "sim.x", "retire": None}


# ---- the count
built = collections.OrderedDict((name, entry(name, kind)) for name, kind in (
    ("A", "temporary_heuristic"), ("B", "temporary_heuristic"), ("C", "hardcoded_outcome"), ("D", "physical_constant")))
with mock.patch.object(constants, "REGISTRY", built), mock.patch.object(constants, "map_heuristics", lambda: ["map_a"]):
    result = constants.burndown()
check("the burndown counts every declared number", result["declared"] == 4, result["declared"])
check("the temporary heuristics are counted and listed apart", result["temporary_heuristics"] == 2
      and [row["name"] for row in result["outstanding"]] == ["A", "B"] and result["share"] == 0.5, result)
check("a hardcoded outcome is listed on its own and not among the heuristics",
      [row["name"] for row in result["historical_outcomes"]] == ["C"] and "C" not in [row["name"] for row in result["outstanding"]], result)
check("the map's heuristic parameters are carried", result["map_heuristics"] == ["map_a"], result)
with mock.patch.object(constants, "REGISTRY", collections.OrderedDict()), mock.patch.object(constants, "map_heuristics", lambda: []):
    empty = constants.burndown()
check("an empty registry reads zero with a share of zero, not a division error", empty["declared"] == 0 and empty["share"] == 0.0, empty)

# ---- declaring a number
with mock.patch.object(constants, "REGISTRY", collections.OrderedDict()) as registry:
    value = constants.declare("_PROBE", 1.5, kind="hardcoded_outcome", unit="test", why="a probe")
    check("declare hands back the number and records it under its kind", value == 1.5 and registry["_PROBE"]["kind"] == "hardcoded_outcome", registry)
    check("declare records the module that called it", registry["_PROBE"]["declared_in"] == __name__, registry["_PROBE"])
    refused = []
    for label, fields in (("an unknown kind", {"kind": "guess", "why": "x"}), ("an unknown confidence", {"kind": "physical_constant", "why": "x", "confidence": "Z"}),
                          ("no reason", {"kind": "physical_constant", "why": "  "})):
        try:
            constants.declare("_BAD", 1.0, unit="test", **fields)
        except ValueError:
            refused.append(label)
    check("declare refuses an unknown kind, an unknown confidence and a missing reason", len(refused) == 3 and "_BAD" not in registry, refused)
    try:
        constants.declare("_PROBE", 2.5, kind="hardcoded_outcome", unit="test", why="a probe")
        twice = False
    except ValueError:
        twice = True
    check("a number declared twice with different values is refused", twice and registry["_PROBE"]["value"] == 1.5, None)
check("hardcoded_outcome is a registered kind", "hardcoded_outcome" in constants.KINDS, None)

# ---- one registry whichever way the file was loaded
local = collections.OrderedDict(((name, entry(name, "physical_constant")) for name in ("LOCAL",)))
canonical = types.SimpleNamespace(REGISTRY=collections.OrderedDict(((name, entry(name, "physical_constant")) for name in ("DECLARED_THROUGH_IMPORT",))))
with mock.patch.dict(sys.modules, {"sim.constants": canonical}), mock.patch.object(constants, "REGISTRY", local):
    constants._adopt_the_canonical_registry()
    adopted = constants.REGISTRY
check("the report reads the canonical registry the imported modules declared into", adopted is canonical.REGISTRY, None)
check("what was declared in this copy is kept in it", sorted(canonical.REGISTRY) == ["DECLARED_THROUGH_IMPORT", "LOCAL"], sorted(canonical.REGISTRY))

# ---- every module that declares numbers is imported by the burndown
# The modules the list names import the others, so which declarations land in the registry is read in a clean process (this one has
# imported far more than the list does), with the import of the burndown's own list run for real.
requested = []
real_import = builtins.__import__


def recording_import(name, *arguments, **keywords):
    if name.startswith("sim."):
        requested.append(name)
    return real_import(name, *arguments, **keywords)


with mock.patch.object(builtins, "__import__", recording_import), mock.patch("builtins.print"):
    constants._import_declaring_modules()
check("the world modules the burndown must count are in the import list", {"sim.world.agriculture", "sim.world.demography"} <= set(requested), requested[:5])
check("the root module of unit conversions is in the import list", "sim.unit_conversions" in requested, None)

# the import loop prints once for each module it cannot import, so the prints made are the failures
script = ("import builtins, sys, json; sys.path.insert(0, %r)\nfrom sim import constants\nreport = builtins.print\nfailures = []\n"
          "builtins.print = lambda *arguments, **keywords: failures.append(arguments)\nconstants._import_declaring_modules()\n"
          "builtins.print = report\nconstants._adopt_the_canonical_registry()\n"
          "report(json.dumps({'failures': len(failures), 'registered': sorted(set(entry['declared_in'] for entry in constants.REGISTRY.values()))}))\n"
          % REPOSITORY_ROOT)
clean = subprocess.run([sys.executable, "-c", script], cwd=REPOSITORY_ROOT, capture_output=True, text=True)
payload = json.loads(clean.stdout.strip() or '{"failures": -1, "registered": []}')
check("the burndown's import of its list imports without a failure", clean.returncode == 0 and payload["failures"] == 0, (payload["failures"], clean.stderr[-300:]))
