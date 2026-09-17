#!/usr/bin/env python3
"""Every number that is not calculated, and where it came from.

    python3 sim/constants.py              what is declared, grouped by provenance
    python3 sim/constants.py --burndown   how much is still a temporary heuristic
    python3 sim/constants.py --kind biological_parameter

THE PROBLEM THIS SOLVES. There are 98 named constants and 1,367 inline numeric
literals across 29 files in this project. Nobody can see a pattern in that. If
somebody wants to change what a person eats in a day they should not have to
find every place that decided it, and the project's central question - what
here is a fundamental fact, and what is a guess we intend to replace - is
unanswerable while the two are mixed into the same expressions.

HOW IT WORKS, AND WHY IT IS A REGISTRY RATHER THAN A FOLDER. The first design
for this put physical constants in one file, biological ones in another,
heuristics in a third, so the file list answered the question by itself. That
is a nice property and it was the wrong trade: a number wants to live beside
the formula that uses it, because moving it away loses the one thing that
makes it defensible, which is the paragraph explaining why it is that number.
Splitting by file also means two authors working on two domains fight over
the same file.

So declarations live next to their use, and `declare` records them centrally.
The provenance split is by the `kind` argument rather than by filename, and
this module prints the grouping on demand. One place to LOOK, without forcing
one place to LIVE.

    CALORIES_PER_PERSON_DAY = declare(
        "CALORIES_PER_PERSON_DAY", 2200.0,
        kind="biological_parameter",
        unit="kcal/person/day",
        source="FAO minimum dietary energy requirement, adult average",
        confidence="B",
        why="Sets how much grain a population must eat before any of its "
            "labour can do anything else. Not a tuning knob: move it and you "
            "are making a claim about human metabolism.")

`declare` returns a plain float, so arithmetic and speed are unchanged and
nothing downstream needs to know this module exists.

THE KINDS, and the only one that matters

    physical_constant        facts about the universe. Densities, melting
                             points, latent heats, Faraday's constant.
    biological_parameter     facts about living things. Calories, gestation,
                             crop growth, mortality curves.
    engineering_estimate     measured facts about technique. Process
                             efficiencies, recovery rates, machine throughput.
    initial_condition        the state of the world at the start. Population
                             in 100 AD, which mines are open, what is known.
    calibration_target       an observation used to CHECK the model. Never an
                             input to it.
    temporary_heuristic      a number we invented because the mechanism that
                             would derive it does not exist yet.

`temporary_heuristic` is the project's progress bar. Every one of them is a
promise to replace it, and `--burndown` counts how many promises are
outstanding. The others are legitimate inputs under CLAUDE.md 3.1 and are not
expected to go away.

WHAT DOES NOT BELONG HERE. Numbers that do not change a simulated outcome.
Column widths, "show the top 5 slowest", retry counts, buffer sizes. Moving
those away from the code that uses them makes that code worse, not better.

A `temporary_heuristic` with an empty `why` fails the check in
sim/tests/test_constants.py. If nobody can say why a number is that number,
that is the most important thing to know about it.
"""
import argparse
import collections
import sys

# name -> metadata. Declaration order is preserved, which makes the report
# stable across runs and diffable.
REGISTRY = collections.OrderedDict()

KINDS = (
    "physical_constant",
    "biological_parameter",
    "engineering_estimate",
    "initial_condition",
    "calibration_target",
    "temporary_heuristic",
)

CONFIDENCES = ("A", "B", "C", "D")


def declare(name, value, kind, unit, why, source=None, confidence="C"):
    """Record a number's provenance and hand back the plain number.

    `name` is passed explicitly and looks redundant next to the assignment it
    is bound to. It earns its place: sim/tests/test_constants.py asserts that
    every declared name matches the module attribute it is actually assigned
    to, so the registry cannot quietly drift out of step with the code. A
    registry that disagrees with the source is worse than no registry.
    """
    if kind not in KINDS:
        raise ValueError("%s: kind must be one of %s, not %r"
                         % (name, ", ".join(KINDS), kind))
    if confidence not in CONFIDENCES:
        raise ValueError("%s: confidence must be one of %s, not %r"
                         % (name, ", ".join(CONFIDENCES), confidence))
    if not (why or "").strip():
        raise ValueError("%s: every declared number needs a `why`. If nobody "
                         "can say why it is that number, that is the most "
                         "important thing to know about it." % name)
    if name in REGISTRY and REGISTRY[name]["value"] != value:
        raise ValueError("%s declared twice with different values (%r, %r)"
                         % (name, REGISTRY[name]["value"], value))
    REGISTRY[name] = {
        "name": name, "value": value, "kind": kind, "unit": unit,
        "source": source, "confidence": confidence, "why": why.strip(),
        "declared_in": _caller_module(),
    }
    return value


def _caller_module():
    frame = sys._getframe(2)
    return frame.f_globals.get("__name__", "?")


def by_kind():
    grouped = collections.OrderedDict((kind, []) for kind in KINDS)
    for entry in REGISTRY.values():
        grouped[entry["kind"]].append(entry)
    return grouped


def burndown():
    """What fraction of declared numbers are promises we have not kept."""
    total = len(REGISTRY)
    heuristics = [e for e in REGISTRY.values()
                  if e["kind"] == "temporary_heuristic"]
    return {"declared": total, "temporary_heuristics": len(heuristics),
            "share": (len(heuristics) / total) if total else 0.0,
            "outstanding": heuristics}


def _import_declaring_modules():
    """Import the modules that declare constants, so the registry fills.

    Kept as an explicit list rather than a directory walk: importing the whole
    package to build a report is a good way to make a reporting tool depend on
    every import in the project working, and this tool should keep running
    when something else is broken.
    """
    for module in ("engine.data",):
        try:
            __import__(module)
        except Exception as exc:                      # noqa: BLE001
            print("  (could not import %s: %s)" % (module, exc),
                  file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--burndown", action="store_true")
    parser.add_argument("--kind", choices=KINDS)
    arguments = parser.parse_args(argv)

    _import_declaring_modules()

    if arguments.burndown:
        result = burndown()
        print("%d numbers declared, %d are temporary heuristics (%.1f%%)"
              % (result["declared"], result["temporary_heuristics"],
                 100.0 * result["share"]))
        if result["outstanding"]:
            print()
            print("Outstanding promises - each of these is a number we invented")
            print("because the mechanism that would derive it does not exist:")
            for entry in result["outstanding"]:
                print("   %-34s %-16s %s" % (entry["name"], entry["unit"],
                                             entry["declared_in"]))
        return 0

    grouped = by_kind()
    for kind, entries in grouped.items():
        if arguments.kind and kind != arguments.kind:
            continue
        print("%s  (%d)" % (kind.upper().replace("_", " "), len(entries)))
        if not entries:
            print("   none declared yet")
        for entry in entries:
            print("   %-34s %-14s %-10s conf %s"
                  % (entry["name"], entry["value"], entry["unit"],
                     entry["confidence"]))
        print()

    if not REGISTRY:
        print("Nothing is declared yet. This is a new mechanism; the 98 named")
        print("constants and 1,367 inline literals measured across the project")
        print("have not been migrated. See docs/architecture/"
              "ENDOGENOUS_COSTS_AND_DOMAINS.md, Milestone 1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
