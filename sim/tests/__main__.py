"""Runner for the split regression suite.

`python3 -m rome.sim.tests` (or `python3 rome/sim/tests/__main__.py`, or the
`rome/sim/test_regressions.py` shim) runs every topic module below, in the
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

# So `python3 rome/sim/tests/__main__.py` (run as a plain script, no package
# context) works exactly like `python3 -m rome.sim.tests`: put the repo root
# on sys.path and import everything below by its absolute dotted name, never
# relatively, so it does not matter whether this module itself was reached
# via -m, via this file's own __main__ guard, or via the test_regressions.py
# shim.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

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
    "dynamic_wages",
    "economic_levers_inventory",
    "explicit_starting_techs",
]


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
    from rome.sim.tests import harness

    print("PLAYTEST REGRESSIONS\n" + "=" * 72)
    for slug in TOPICS:
        if slug in selected:
            importlib.import_module("rome.sim.tests.test_%s" % slug)

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
