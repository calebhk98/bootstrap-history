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

HOW IT WORKS, AND WHY IT IS A REGISTRY RATHER THAN A FOLDER. Grouping
constants into files by kind - physical constants in one file, biological
ones in another, heuristics in a third - would separate a number from the
formula that uses it, losing the one thing that makes it defensible: the
paragraph explaining why it is that number. It would also mean two authors
working on two domains fight over the same file.

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

THE KINDS, and the two that matter for different reasons

    physical_constant        facts about the universe. Densities, melting
                             points, latent heats, Faraday's constant. Also
                             covers exact, definitional unit conversions
                             (kilograms per tonne, metres per kilometre,
                             percent) - true by construction rather than by
                             measurement, but not a distinct kind of their
                             own: see sim/unit_conversions.py's own module
                             docstring for why. HOURS_PER_YEAR (sim/
                             engine/economy_electricity.py) and DAYS_PER_YEAR
                             (sim/world/demand.py) are declared the same way,
                             at confidence "A".
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
    hardcoded_outcome
                             a number that IS the answer to something the
                             simulation is supposed to compute - a price, a
                             wage, an interest rate, a tax rate - copied in
                             from the historical record instead. CLAUDE.md
                             SS3.1 forbids this outright. See Complaints/36.

`temporary_heuristic` is the project's progress bar: every one of them is a
promise to replace it, and it will always have a tail, because "no mechanism
exists yet" is a permanent feature of an unfinished migration, not a bug.
`hardcoded_outcome` is a DIFFERENT progress bar with a different
target: `--burndown` expects it to reach EXACTLY ZERO, because unlike an
un-derived heuristic, a live SS3.1 violation is not something this project
tolerates having a tail of. Complaints/36 records why treating these two
kinds as one bucket hid the second, much smaller and much more urgent one.

    python3 sim/constants.py --burndown       prints the live count
    grep -rn 'kind="hardcoded_outcome"' --include=*.py sim/ | wc -l

Deliberately stated as a command rather than a number in prose: the whole
point of this kind is that the count should be falling, so a figure quoted
here goes stale the moment somebody fixes one. See CLAUDE.md SS8: a number
in prose carries the command that produced it, or it does not go in.

The remaining kinds are legitimate inputs under CLAUDE.md 3.1 and are not
expected to go away.

WHAT DOES NOT BELONG HERE. Numbers that do not change a simulated outcome.
Column widths, "show the top 5 slowest", retry counts, buffer sizes -
gathered instead in `sim/presentation.py`, a DIFFERENT kind of file serving
a DIFFERENT purpose (see that module's own THE TENSION WITH sim/
constants.py section for why one stakeholder request to "gather these
somewhere editable" does not actually conflict with the sentence you are
reading, once the two are told apart). This registry is a provenance tool
for numbers that make a claim on the simulated world; a column width makes
no such claim and was never what this paragraph meant to protect by
staying scattered. Unit conversions (kilograms per tonne, metres per
kilometre, percent) get the same "not by oversight" treatment in `sim/
unit_conversions.py`, and solver mechanics (damping factors, convergence
tolerances, iteration ceilings) in `sim/algorithm_parameters.py` - three
siblings to this file, none of them calling `declare()`, each explaining in
its own docstring why its own numbers do not belong in the registry `--
burndown` measures. Moving a genuine formula-adjacent number away from the
code that uses it still makes that code worse, not better - that half of
this paragraph is unchanged and is the reason none of those three files
holds anything BUT the categories named above.

A `temporary_heuristic` with an empty `why` fails the check in
sim/tests/test_constants.py. If nobody can say why a number is that number,
that is the most important thing to know about it.
"""
import argparse
import collections
import os
import sys
import types

# Root the imports at the REPOSITORY, not at sim/, so a module that calls
# declare() can be reached by its full dotted name (sim.world.agriculture)
# regardless of how this file was invoked. Same rooting, and the same reason,
# as sim/tests/__main__.py: `sim` is a PEP 420 namespace package, so this
# works from any directory under any checkout name with no packaging
# metadata. Without it, _import_declaring_modules() below silently fails
# every import and the burndown reports zero.
_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPOSITORY_ROOT not in sys.path:
    sys.path.insert(0, _REPOSITORY_ROOT)

_SIM_ROOT = os.path.dirname(os.path.abspath(__file__))
while _SIM_ROOT in sys.path:
    sys.path.remove(_SIM_ROOT)

# name -> metadata. Declaration order is preserved, which makes the report
# stable across runs and diffable.
# ONE REGISTRY, HOWEVER MANY TIMES THIS FILE IS LOADED.
#
# This repository has TWO import roots and this file sits in both. The engine
# is imported rooted at sim/, so it reaches this file as `constants`. The
# sim/world/ modules and the test runner are rooted at the REPOSITORY, so they
# reach the same file as `sim.constants`. Running it as a script makes a third,
# `__main__`. Each of those is a separate module object with its own globals,
# so a plain `REGISTRY = OrderedDict()` gives each one its own empty dict - the
# declarations land in one and the report reads another, and --burndown prints
# a number that is quietly too low.
#
# Stashing the dict in sys.modules under a name nothing else can claim makes
# every copy of this module share one object, whatever it is imported as. This
# is not a compatibility shim of the kind CLAUDE.md 3.5 forbids - it is not
# about old data, it is about one dict having one home.
_REGISTRY_HOME_KEY = "_bootstrap_history_constants_registry"
if _REGISTRY_HOME_KEY in sys.modules:
    REGISTRY = sys.modules[_REGISTRY_HOME_KEY].REGISTRY
else:
    _registry_home = types.ModuleType(_REGISTRY_HOME_KEY)
    _registry_home.REGISTRY = collections.OrderedDict()
    sys.modules[_REGISTRY_HOME_KEY] = _registry_home
    REGISTRY = _registry_home.REGISTRY

KINDS = (
    "physical_constant",
    "biological_parameter",
    "engineering_estimate",
    "initial_condition",
    "calibration_target",
    "temporary_heuristic",
    # THE TEST IS NOT PROVENANCE, IT IS WHETHER THE QUANTITY IS AN OUTPUT.
    # Ask: is this quantity something the simulation is supposed to COMPUTE?
    # A price, a wage, a rent, an interest rate, a city size, a recovery
    # time - CLAUDE.md SS3.1's own headline example is what a Roman soldier
    # costs - are outputs, and asserting one is the violation however
    # defensible the number. An INVENTED number is not more defensible than
    # a copied one; if anything it is worse, because at least a copied
    # number is right about the world. An elasticity, a decay rate, a curve
    # shape are inputs: nobody expects the model to derive them from
    # anything, so they are temporary_heuristic and always will be.
    #
    # A label narrower than its own test is worse than no label, because it
    # reads as permission.
    "hardcoded_outcome",
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
    """What fraction of declared numbers are promises we have not kept.

    Reports two separate counts, because they are two separate promises with
    two separate expected endings - see this module's THE KINDS section.
    `temporary_heuristics` will always have a tail; `historical_outcomes` is
    expected to hit zero, and until it does it is the more important of the
    two numbers, so callers should look at it FIRST.
    """
    total = len(REGISTRY)
    heuristics = [entry for entry in REGISTRY.values()
                  if entry["kind"] == "temporary_heuristic"]
    historical_outcomes = [entry for entry in REGISTRY.values()
                            if entry["kind"] == "hardcoded_outcome"]
    return {"declared": total, "temporary_heuristics": len(heuristics),
            "share": (len(heuristics) / total) if total else 0.0,
            "outstanding": heuristics,
            "historical_outcomes": historical_outcomes}


def _adopt_the_canonical_registry():
    """Make this module share `sim.constants`'s REGISTRY, not its own copy.

    THE BUG THIS EXISTS FOR. Running `python3 sim/constants.py` loads this
    file as `__main__`. The modules it then imports do `from sim.constants
    import declare`, which loads the SAME FILE AGAIN under the name
    `sim.constants` - a second, separate module object with a second, separate
    REGISTRY dict. Their declarations filled that one; the report printed this
    one; it said "0 numbers declared" while 32 sat in the other copy.

    Nothing looked broken. There was no traceback and no warning, and zero had
    been the correct answer on the day the tool was written, so the number
    stayed believable for as long as nobody checked it against the source.
    That is the same shape as the other silent successes on this branch: the
    tool reported, the report was wrong, and the wrongness was invisible
    because it agreed with what you expected.

    The fix is to point this module's REGISTRY at the canonical module's, so
    both names refer to one dict and it does not matter which copy anything
    declared into.
    """
    global REGISTRY
    canonical = sys.modules.get("sim.constants")
    if canonical is not None and canonical is not sys.modules.get("__main__"):
        if canonical.REGISTRY is not REGISTRY:
            canonical.REGISTRY.update(REGISTRY)
            REGISTRY = canonical.REGISTRY


def _import_declaring_modules():
    """Import the modules that declare constants, so the registry fills.

    Kept as an explicit list rather than a directory walk: importing the whole
    package to build a report is a good way to make a reporting tool depend on
    every import in the project working, and this tool should keep running
    when something else is broken.
    """
    # THE RULE WHEN YOU ADD A MODULE THAT CALLS declare(): add it here in the
    # same commit, or its numbers do not exist as far as the burndown knows.
    # A module missing from this list does not error - it silently reports
    # fewer declared numbers than actually exist, which is worse than an
    # obvious failure, because a scoreboard that cannot tell progress from no
    # progress is quietly believed.
    #
    # Still an explicit list rather than a directory walk, for the reason
    # above: this tool should keep reporting when something else is broken.
    # sim.unit_conversions is at the REPOSITORY root, not under sim/world/,
    # so sim/tests/test_constants_burndown.py's own
    # test_every_declaring_module_under_sim_world_is_in_the_list cannot
    # catch this one going missing the way it catches a sim/world/ file -
    # there is no directory walk for sim/ root modules, on purpose, for the
    # same "keep the tool running when something else is broken" reason the
    # sim/world/ list below is explicit rather than walked. Whoever adds the
    # next sim/-root file that calls declare() has to add it here by hand.
    # sim/presentation.py and sim/algorithm_parameters.py are siblings that
    # do NOT belong in this list, because neither calls declare() at all
    # (see either module's own NOT PART OF THE REGISTRY / kind section for
    # why).
    for module in ("sim.engine.data",
                   "sim.engine.economy",
                   "sim.engine.cli",
                   "sim.engine.core",
                   "sim.engine.society",
                   "sim.engine.labour",
                   "sim.engine.projects",
                   "sim.unit_conversions",
                   "sim.world.agriculture",
                   "sim.world.demography",
                   "sim.world.shared_constants",
                   "sim.world.transport",
                   "sim.world.military_logistics",
                   "sim.world.deposits",
                   "sim.world.land",
                   "sim.world.demand",
                   "sim.world.labour_market"):
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
    _adopt_the_canonical_registry()

    if arguments.burndown:
        result = burndown()
        outcomes = result["historical_outcomes"]
        # This first line is a stable contract: sim/tests/test_constants_
        # burndown.py's own subprocess checks read stdout.split()[0] as the
        # total declared count, and that must keep working. The HARDCODED
        # HISTORICAL OUTCOME section below it is reported separately and
        # loudly, not first, so both stay true at once.
        print("%d numbers declared, %d are temporary heuristics (%.1f%%)"
              % (result["declared"], result["temporary_heuristics"],
                 100.0 * result["share"]))
        print()
        # SEPARATE FROM temporary_heuristic, ON PURPOSE, AND REPORTED LOUDLY.
        # See Complaints/36: treating the two as one bucket meant a queue
        # where "invent a better elasticity eventually" and "a SS3.1
        # violation is live in the shipping model" sorted identically, which
        # is not measurable in the way that matters. Unlike temporary_heuristic
        # above - which will always have a tail - THIS COUNT IS EXPECTED TO
        # REACH ZERO. It is a defect list, not a progress bar.
        print("=" * 72)
        print("%d HARDCODED OUTCOME%s (CLAUDE.md SS3.1 forbids "
              "these outright)"
              % (len(outcomes), "" if len(outcomes) == 1 else "S"))
        print("Expected count: ZERO. Every one of these is a live SS3.1 "
              "violation, not scaffolding.")
        if outcomes:
            for entry in outcomes:
                print("   %-34s %-16s %s" % (entry["name"], entry["unit"],
                                             entry["declared_in"]))
        else:
            print("   (none currently declared)")
        print("=" * 72)
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
