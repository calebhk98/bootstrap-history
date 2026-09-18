"""Runner for the split regression suite.

`python3 -m sim.tests` (or `python3 sim/tests/__main__.py`, or the
`sim/test_regressions.py` shim) runs every topic module below, in the
same order test_regressions.py always ran them in, and prints the same
summary line it always has. `--only economy,labour` (comma-separated topic
names, matching this list) runs just those modules - everything else about
the run (the harness, --slow, --jobs) is unchanged. `--list` prints the
topic names and exits.
"""
import importlib
import json
import os
import sys
import unittest

# So `python3 sim/tests/__main__.py` (run as a plain script, no package
# context) works exactly like `python3 -m sim.tests`: put the repo root on
# sys.path and import everything below by its absolute dotted name, never
# relatively, so it does not matter whether this module itself was reached
# via -m, via this file's own __main__ guard, or via the test_regressions.py
# shim.
#
# THE DOTTED NAME USED TO BE `rome.sim.tests`, WHICH MEANT THE SUITE ONLY RAN
# IF THE CHECKOUT DIRECTORY WAS NAMED `rome`. It is named bootstrap-history on
# GitHub, so a fresh clone could not run its own tests: the import died on
# ModuleNotFoundError before a single check executed. `sim` is a PEP 420
# namespace package (no __init__.py) and `sim.tests` a regular one, so
# rooting the import at the repository instead of at its parent works from
# any directory, under any name, with no packaging metadata.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Original test_regressions.py's own top-to-bottom order. A topic file's
# name records which of the file's own section banners it came from - see
# each module's own docstring for the exact original line range.
TOPICS = [
    "early_playtest",
    "round2_policy_hazards_options",
    "literacy_market_pricing",
    "commodities_wired_in",
    "round8_fixes",
    "round9",
    "round10",
    "historical_events",
    "names_and_fog",
    "player_log",
    "goods_market",
    "mines",
    "reputation",
    "people_attrition_scholars",
    "interface_honesty",
    "fog_leak3",
    "parallelism_note",
    "sort_nearest",
    "labour_productivity",
    "arrears_hours",
    "hedge_chain",
    "market_saturation",
    "round8g_display",
    "five_things_winner",
    "industrial_dashboard",
    "scanners_and_scheduling",
    "round12_naive15",
    "affordability_warning",
    "arrears_visibility",
    "allocate",
    "craftsmen_wording",
    "demographics",
    # Focused complaint suites are first-class regressions too.  These used to
    # exist on disk without appearing here, so the documented full-suite
    # command silently skipped the fixes they were written to protect.
    "complaints_09_16",
    "complaint_13_specialist_supervision",
    "complaints_17_24",
    # Complaints/34: commissioned SCHOLAR hours bought nothing, because the
    # project gate read the standing headcount. The same defect
    # craft_hands_available() was written to fix, never extended to scholars.
    "complaint_34_scholar_hours",
    # Complaints/38: `path` printed one founder-hours budget and judged
    # feasibility against a different one. The test asserts the printed and
    # judged figures share a SOURCE, not merely that they currently agree.
    "complaint_38_founder_lifetime",
    # sim/engine/proto/: the agent-oriented compact output mode asked for in
    # Complaints/35 section 1 - structured state WITHOUT losing the
    # reason-carrying prose. Includes the byte-identical proof that the
    # mode-off path is unchanged.
    "compact_mode",
    "dynamic_wages",
    "economic_levers_inventory",
    "explicit_starting_techs",
    "realism_part02",
    "realism_part03",
    "realism_part04",
    "realism_part05",
    # Written as unittest.TestCase classes rather than top-level check() calls;
    # _run_topic handles both. It had never run: unregistered here, and unable
    # to import under the old rome.sim.tests rooting even if it had been.
    "tierless_schema",
    # sim/world/agriculture.py: land, labour, technique and weather into
    # food, standalone and with no import of sim/engine/ - see that
    # module's own docstring for why. Also unittest.TestCase-style.
    "agriculture",
    # sim/world/demography.py: age-cohort population dynamics, standalone
    # and with no import of sim/engine/ - see that module's own docstring
    # for why, and sim/world/__init__.py for the package as a whole. Also
    # unittest.TestCase-style.
    "demography",
    # WIRING MILESTONE 4's seam: sim/engine/core.py's Sim._demographic_
    # recovery now feeds sim/world/agriculture.py's real land+labour+weather
    # harvest to sim/world/demography.py's Population.step, replacing a
    # stand-in that assumed nutrition_ratio == 1.0 every year. Neither
    # agriculture nor demography's own standalone suite can see this seam -
    # each proves its own module correct in isolation, and the seam does
    # not exist inside either module - so this is the one place a famine
    # actually falling out of land/labour/weather/population, rather than
    # a scripted hazard, is checked end to end. Depends on sim/engine/, so
    # unlike agriculture/demography above it is NOT standalone. Also
    # unittest.TestCase-style.
    "agriculture_wiring",
    # sim/world/military_logistics.py: rations, fodder, baggage-train range
    # and firearm ammunition/maintenance as consumption arithmetic,
    # standalone and with no import of sim/engine/ or the other sim/world/
    # modules - see that module's own docstring for why. Also
    # unittest.TestCase-style.
    "military_logistics",
    # sim/world/transport.py: freight cost per tonne-km from draught-animal
    # metabolism, rolling resistance and gradient, standalone and with no
    # import of sim/engine/ or the other sim/world/ modules - see that
    # module's own docstring for why. Also unittest.TestCase-style.
    "transport",
    # sim/tests/test_material_freight.py: the crossing that wires transport.py
    # into sim/engine/economy.py - a live Sim, through geography.json's own
    # per-region `minerals` table, not standalone like "transport" above.
    # Flat check()-at-import style, like most other topics.
    "material_freight",
    # sim/world/deposits.py: Ricardian rent (marginal-deposit pricing) from
    # ore grade, depth and hardness, standalone and with no import of
    # sim/engine/ or the other sim/world/ modules - see that module's own
    # docstring for why and Complaints/32 for the gap it closes. Also
    # unittest.TestCase-style.
    "deposits",
    # sim/world/demand.py: households with budgets and a Stone-Geary/LES
    # demand system, plus derived (producer) demand read straight from
    # data/production/*.json - standalone and with no import of sim/engine/
    # or any other sim/world/ module - see that module's own docstring for
    # why. Also unittest.TestCase-style.
    "demand",
    # docs/architecture/DEMAND_AT_SCALE.md: pins two structural defects in
    # the demand system - the hard subsistence cliff and the Engel-curve
    # floor - in the "assert the wrong behaviour, invert don't delete"
    # style test_price_solver_cycles.py used before Complaints/31 was fixed.
    "demand_at_scale",
    # Guards the two silent bugs that made --burndown print "0 numbers
    # declared" while 32 were declared, which left milestone 1 unmeasurable.
    "constants_burndown",
    # Pins Complaints/31: the price solver's resolvability pass refuses
    # every recipe cycle, including the axe/iron example its own docstring
    # uses. Written as assertions on the CURRENT wrong behaviour so the
    # suite stays green and the defect stays impossible to miss.
    "price_solver_cycles",
    # Pins the technique-to-node link the price solver gates on. The tree
    # records what a node CONSUMES and never what anything produces, so
    # nothing joined a production recipe to the node that lets anyone run
    # it, and the solve had no way to tell a Roman technique from a modern
    # one. See Complaints/39 for the run that exposed it.
    "price_solver_era_gate",
    # Complaints/32's own follow-up: the solver printed RENT_IS_ZERO on
    # every run although sim/world/deposits.py's Ricardian marginal-deposit
    # model sat unimported next to it. Pins rent_hours_per_kg_by_ore_material
    # (the demand-fixed-exogenously heuristic that closes the loop) and the
    # iron blast-furnace/bloomery fallback --civ rome_100ad actually
    # exercises.
    "price_solver_rent",
    # The last of the five standalone sim/world/ modules to be wired.
    # military_logistics.py derives what a soldier's iron and ammunition
    # cost to keep supplied, in KILOGRAMS - deliberately never converted to
    # money, because a mass-to-currency conversion would need a price this
    # crossing has no business inventing.
    "military_logistics_wiring",
    # Complaints/30 stage 3: a branch edit to an EXISTING tech-tree node was
    # silently discarded, so data/branches/ was decorative for every id the
    # tree already carried. Pins the field-by-field overlay, the fixed point
    # (no edits means byte-identical output), and the new rule that an id
    # defined in two branch files is an error naming both sides.
    "branch_merge_authority",
    # sim/engine/prices.py: the first wiring of the price solver into the
    # engine - given a set of held technology ids, ask the solver for a
    # price, cached on the gate nodes held rather than the full technology
    # set, with data/prices.json as the fallback and a per-material
    # provenance report ("solved" or "book") as the measurable burndown.
    # Off by default; sim/engine/data.py's load() only calls it when
    # use_solved_prices=True. See that module's own docstring.
    "engine_prices",
    # Complaints/42: a civilisation holding a node whose own prerequisites it
    # lacks. Seventeen do. Pinned by name rather than fixed, and failing in
    # both directions, so the count can only move deliberately.
    "civilisation_prerequisites",
    # Guards the id()-reuse hazard that made the simulation non-deterministic;
    # structural, so it catches the class rather than the one instance.
    "determinism",
    # The tool that makes the naming sweep affordable; verified here because a
    # verification tool nobody verified is a rubber stamp.
    "rename_prover",
    # The suite has to be able to run before anything above it can:
    # this topic checks that it does so from a checkout of any name,
    # in any directory. It is last because it re-runs one cheap topic
    # in a child process.
    "suite_portability",
]


def _run_topic(slug, harness):
    """Import one topic module, and run it whichever style it is written in.

    Almost every topic module is plain top-level code calling check() at import
    time, so importing it IS running it. One - tierless_schema - is written as
    unittest.TestCase classes instead, which import cleanly and then do
    nothing. It sat in sim/tests/ unregistered and unrun for its whole life,
    and it could not have run even if registered: it does `from sim import
    treetool`, which needed the repository root on sys.path, which is exactly
    what the old `rome.sim.tests` rooting did not provide.

    Rather than rewrite six working tests into the other style, the runner
    accepts both. Each TestCase method becomes one check, so a unittest topic
    reports in the same summary, the same count, and the same exit code as
    every other topic.
    """
    mod = importlib.import_module("sim.tests.test_%s" % slug)

    cases = unittest.TestLoader().loadTestsFromModule(mod)
    if not cases.countTestCases():
        return

    for case in _flatten(cases):
        result = unittest.TestResult()
        case.run(result)
        problems = result.errors + result.failures
        harness.check(
            "%s: %s" % (slug, case.id().rsplit(".", 1)[-1].replace("_", " ")),
            not problems,
            problems[0][1].strip().splitlines()[-1] if problems else "")


def _flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            for sub in _flatten(item):
                yield sub
        else:
            yield item


def _parse_only(argv):
    for i, a in enumerate(argv):
        if a == "--only" and i + 1 < len(argv):
            return [t.strip() for t in argv[i + 1].split(",") if t.strip()]
        if a.startswith("--only="):
            return [t.strip() for t in a.split("=", 1)[1].split(",") if t.strip()]
    return None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if "--list" in argv:
        for slug in TOPICS:
            print(slug)
        return 0

    only = _parse_only(argv)
    if only is None:
        selected = list(TOPICS)
    else:
        selected = only
        unknown = [t for t in selected if t not in TOPICS]
        if unknown:
            sys.stderr.write("unknown topic(s): %s\n" % ", ".join(unknown))
            sys.stderr.write("run --list to see topic names\n")
            return 2

    # Imported here (not at module scope) so --list works even if a topic
    # module fails to import, and so the harness (whose --jobs/--slow parsing
    # reads sys.argv at import time) sees the same sys.argv main() was called
    # with, exactly as when this was all one flat script. Absolute dotted
    # names throughout (never a relative "from . import"), so this runs the
    # same way whether reached via -m, via this file's own __main__ guard,
    # or via the test_regressions.py shim.
    from sim.tests import harness

    print("PLAYTEST REGRESSIONS\n" + "=" * 72)
    for slug in TOPICS:
        if slug in selected:
            _run_topic(slug, harness)

    print("=" * 72)
    print("%d checks, %d failures, %.0fs%s"
          % (len(harness.CHECKS_RUN), len(harness.FAILURES),
             sum(t for _, t in harness.CHECKS_RUN),
             ("   (%d slow checks skipped: run with --slow)" % len(harness.SKIPPED))
             if harness.SKIPPED else ""))
    slow = sorted(harness.CHECKS_RUN, key=lambda r: -r[1])[:5]
    if slow and slow[0][1] >= 5.0:
        print("slowest:")
        for nm, t in slow:
            if t >= 5.0:
                print("   %5.0fs  %s" % (t, nm))
    for f in harness.FAILURES:
        print("   FAILED:", f)
    print("subprocess spawns: %d calls, %.0fs waiting on child processes"
          % (harness._SUBPROC_CALLS[0], harness._SUBPROC_TIME[0]))
    if harness._PROFILE_OUT:
        with open(harness._PROFILE_OUT, "w") as _pf:
            json.dump({"checks": harness.CHECKS_RUN,
                       "subproc_time": harness._SUBPROC_TIME[0],
                       "subproc_calls": harness._SUBPROC_CALLS[0],
                       "total_wall": sum(t for _, t in harness.CHECKS_RUN)}, _pf)
    return 1 if harness.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
