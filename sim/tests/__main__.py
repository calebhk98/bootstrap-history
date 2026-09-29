"""Runner for the split regression suite.

`python3 -m sim.tests` (or `python3 sim/tests/__main__.py`, or the
`sim/test_regressions.py` shim) runs every sim/tests/test_*.py topic in
sorted order, discovered from disk (nothing is registered), and prints a
summary line. `--only economy,labour` (comma-separated topic
names, as `--list` prints them) runs just those modules - everything else about
the run (the harness, --slow, --jobs) is unchanged. `--list` prints the
topic names and exits.

`--timing` adds a per-topic table to the summary: wall seconds, share of
the run, and how many checks each topic bought. That table is what decides
whether a topic deserves a module-level `SLOW_TOPIC = True`. It changes
nothing about which checks run, so `--timing` can be added to any
invocation, including `--only` and `--slow`.

`--jobs N` (default: available cores; `--jobs 1` is the plain sequential run)
runs each topic in its own fresh worker process, N at a time. Each worker
buffers its output and the runner prints topics in the sorted order, so the
output is the same as `--jobs 1` apart from timings. Workers run with
`--jobs 1` inside, so in-topic subprocess parallelism does not multiply with
topic parallelism, and each gets its own scratch directories. A topic that
must not run beside others sets a module-level `SERIAL_TOPIC = True`; those
run one at a time after the parallel batch. Per-topic times are remembered
in `.cache/` so the next run starts the longest topics first.
"""
import importlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

# So `python3 sim/tests/__main__.py` (run as a plain script, no package
# context) works exactly like `python3 -m sim.tests`: put the repo root on
# sys.path and import everything below by its absolute dotted name, never
# relatively, so it does not matter whether this module itself was reached
# via -m, via this file's own __main__ guard, or via the test_regressions.py
# shim.
#
# THE DOTTED NAME MUST NOT DEPEND ON THE CHECKOUT'S DIRECTORY NAME: rooting
# it at `rome.sim.tests` would mean the suite only runs if the checkout
# directory is named `rome`. It is named bootstrap-history on GitHub, so a
# fresh clone would not be able to run its own tests: the import would die
# on ModuleNotFoundError before a single check executed. `sim` is a PEP 420
# namespace package (no __init__.py) and `sim.tests` a regular one, so
# rooting the import at the repository instead of at its parent works from
# any directory, under any name, with no packaging metadata.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from sim.tests.discovery import discover_topics  # noqa: E402

# Every sim/tests/test_*.py is a topic, in sorted order (see discovery.py).
TOPICS = discover_topics()


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
        # WRAPPED IN A ONE-CASE SUITE, NOT `case.run(result)` DIRECTLY.
        # Running a TestCase instance straight bypasses setUpClass and
        # tearDownClass entirely - those are invoked by the SUITE, not by
        # the case - so a module using the ordinary unittest idiom
        #
        #     @classmethod
        #     def setUpClass(cls): cls.data = load()
        #
        # came back with AttributeError on every single test here, while
        # passing perfectly under `python3 -m unittest`. That combination is
        # the worst kind of trap: an author verifies with the standard tool,
        # sees green, and only this runner disagrees. It cost one agent a
        # whole test module before it was noticed, and three modules in this
        # directory already use the idiom.
        #
        # TestSuite.run does the class fixture handling, so a one-case suite
        # gets it right. The cost is that setUpClass runs once per test
        # rather than once per class, which is correct-but-slower; every
        # current user of it loads a JSON file, so it does not matter. If a
        # module ever needs a genuinely expensive class fixture, group by
        # class here instead of paying it per test.
        unittest.TestSuite([case]).run(result)
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


def _print_topic_timing(topic_costs):
    """Print what each topic module cost, most expensive first.

    This is the evidence harness.SLOW_TOPICS is supposed to rest on, and
    until now it did not exist as anything you could run. Three columns:
    wall seconds, share of the measured total, and how many checks that
    bought. The third column is the one that stops this table being used
    badly. A topic costing 8% of the run is worth deferring if it is 6
    checks; the same 8% is not worth deferring if it is 394, because
    deferring it means a default run stops proving 394 things, and a suite
    that is fast because it checks less is not faster, it is weaker. That
    trade is exactly why the two topics replaced during the subject-based
    regrouping did NOT get the slow tag passed on to their successors.

    Shares are of the sum of the per-topic figures rather than of the
    process's own wall clock, so they add to 100% and stay comparable
    between a full run and an --only run. Everything outside a topic (the
    harness import, argument parsing, the summary itself) is therefore not
    in the denominator; it is a fraction of a second and counting it would
    make two runs with different topic selections incomparable.
    """
    measured_total = sum(seconds for _, seconds, _ in topic_costs)
    if not measured_total:
        return
    print("per-topic timing (--timing), most expensive first:")
    print("   %8s %7s %7s  %s" % ("seconds", "share", "checks", "topic"))
    for slug, seconds, check_count in sorted(topic_costs,
                                             key=lambda row: -row[1]):
        print("   %8.2f %6.1f%% %7d  %s"
              % (seconds, 100.0 * seconds / measured_total, check_count, slug))
    print("   %8.2f %6.1f%% %7d  (%d topics measured)"
          % (measured_total, 100.0,
             sum(count for _, _, count in topic_costs), len(topic_costs)))


_TIMES_FILE = os.path.join(_REPO_ROOT, ".cache", "test_topic_seconds.json")


def _load_topic_seconds():
    try:
        with open(_TIMES_FILE, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def _save_topic_seconds(topic_costs):
    """Remember per-topic wall time so the next parallel run starts the longest first."""
    known = _load_topic_seconds()
    known.update({slug: seconds for slug, seconds, _ in topic_costs})
    try:
        os.makedirs(os.path.dirname(_TIMES_FILE), exist_ok=True)
        handle_fd, temporary = tempfile.mkstemp(dir=os.path.dirname(_TIMES_FILE), suffix=".tmp")
        with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
            json.dump(known, handle)
        os.replace(temporary, _TIMES_FILE)
    except OSError:
        pass


def _worker_main(slug, result_path):
    """Run one topic in this (fresh) process and dump its results as JSON."""
    from sim.tests import harness
    checks_before = len(harness.CHECKS_RUN)
    started_at = time.time()
    _run_topic(slug, harness)
    with open(result_path, "w", encoding="utf-8") as handle:
        json.dump({"seconds": time.time() - started_at,
                   "checks": harness.CHECKS_RUN[checks_before:],
                   "failures": harness.FAILURES,
                   "skipped": harness.SKIPPED,
                   "subproc_time": harness._SUBPROC_TIME[0],
                   "subproc_calls": harness._SUBPROC_CALLS[0]}, handle)
    return 0


def _start_worker(slug, harness, result_dir):
    """Launch a fresh process for one topic; in-topic parallelism is 1 per worker."""
    result_path = os.path.join(result_dir, slug + ".json")
    command = [sys.executable, os.path.abspath(__file__), "--worker", slug,
               "--worker-result", result_path, "--worker-tag", slug, "--jobs", "1"]
    if harness.SLOW:
        command.append("--slow")
    completed = harness._real_subprocess_run(command, capture_output=True, text=True,
                                             cwd=_REPO_ROOT)
    result = None
    try:
        with open(result_path, encoding="utf-8") as handle:
            result = json.load(handle)
    except (OSError, ValueError):
        pass
    return completed, result


def _run_topics_parallel(run_now, harness, jobs):
    """Run topics in worker processes; print and merge results in topic order."""
    serial = set(harness.SERIAL_TOPICS)
    seconds_before = _load_topic_seconds()
    parallel_slugs = sorted((slug for slug in run_now if slug not in serial),
                            key=lambda slug: -seconds_before.get(slug, 0.0))
    serial_slugs = [slug for slug in run_now if slug in serial]
    topic_costs = []
    outcomes = {}
    with tempfile.TemporaryDirectory(prefix="rome_suite_") as result_dir:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = {slug: pool.submit(_start_worker, slug, harness, result_dir)
                       for slug in parallel_slugs}
            # Serial topics wait for the whole parallel batch, then run one at a time.
            for future in futures.values():
                future.exception()
        for slug in serial_slugs:
            outcomes[slug] = _start_worker(slug, harness, result_dir)
        for slug, future in futures.items():
            outcomes[slug] = future.result()
    for slug in run_now:
        completed, result = outcomes[slug]
        sys.stdout.write(completed.stdout)
        if result is None:
            message = "%s: worker crashed (exit %s)" % (slug, completed.returncode)
            print("  %-58s FAIL %s" % (message, completed.stderr.strip()[-400:]))
            harness.CHECKS_RUN.append((message, 0.0))
            harness.FAILURES.append(message)
            topic_costs.append((slug, 0.0, 1))
            continue
        harness.CHECKS_RUN.extend((name, took) for name, took in result["checks"])
        harness.FAILURES.extend(result["failures"])
        harness.SKIPPED.extend(result["skipped"])
        harness._SUBPROC_TIME[0] += result["subproc_time"]
        harness._SUBPROC_CALLS[0] += result["subproc_calls"]
        topic_costs.append((slug, result["seconds"], len(result["checks"])))
    _save_topic_seconds(topic_costs)
    return topic_costs


def _parse_only(argv):
    for i, arg in enumerate(argv):
        if arg == "--only" and i + 1 < len(argv):
            return [topic.strip() for topic in argv[i + 1].split(",") if topic.strip()]
        if arg.startswith("--only="):
            return [topic.strip() for topic in arg.split("=", 1)[1].split(",") if topic.strip()]
    return None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if "--list" in argv:
        for slug in TOPICS:
            print(slug)
        return 0

    if "--worker" in argv:
        position = argv.index("--worker")
        result_path = argv[argv.index("--worker-result") + 1]
        return _worker_main(argv[position + 1], result_path)

    only = _parse_only(argv)
    if only is None:
        selected = list(TOPICS)
    else:
        selected = only
        unknown = [topic for topic in selected if topic not in TOPICS]
        if unknown:
            sys.stderr.write("unknown topic(s): %s\n" % ", ".join(unknown))
            sys.stderr.write("run --list to see topic names\n")
            return 2

    # Imported here (not at module scope) so --list works even if a topic
    # module fails to import, and so the harness (whose --jobs/--slow parsing
    # reads sys.argv at import time) sees the real sys.argv main() was
    # called with. Absolute dotted names throughout (never a relative
    # "from . import"), so this runs the
    # same way whether reached via -m, via this file's own __main__ guard,
    # or via the test_regressions.py shim.
    from sim.tests import harness

    # SLOW TOPICS ARE OPT-IN, THE SAME WAY SLOW CHECKS ARE: same --slow flag
    # / ROME_SLOW_TESTS env var harness.py already reads, one grain coarser.
    # Naming a topic with --only is itself an explicit request for it, so a
    # topic in harness.SLOW_TOPICS still runs when the person asked for it by
    # name - only the DEFAULT (no --only) run skips it. Nobody should have to
    # pass --slow and --only together just to get a topic they already named.
    skipped_slow_topics = ([slug for slug in selected
                             if slug in harness.SLOW_TOPICS] if only is None and not harness.SLOW
                            else [])
    run_now = [slug for slug in selected if slug not in skipped_slow_topics]

    print("PLAYTEST REGRESSIONS\n" + "=" * 72)
    # PER-TOPIC WALL TIME, MEASURED HERE AND NOWHERE ELSE. harness.check()
    # times each individual CHECK (as the gap since the previous one, which
    # is why a topic module's import-time work lands on its own first check
    # rather than vanishing). That is the right grain for finding one
    # expensive check inside a cheap topic. It is the wrong grain for the
    # decision harness.SLOW_TOPICS actually encodes, which is whether a WHOLE
    # TOPIC MODULE is worth opting out of a default run.
    #
    # harness.SLOW_TOPICS' own percentages need a real command producing the
    # number, not a hand-run measurement nothing re-checks: a figure taken by
    # hand once and thrown away is unreproducible from the moment it is
    # written and drifts silently thereafter. CLAUDE.md section 8 says a
    # number in prose carries the command that produced it or it does not go
    # in. This loop is that command.
    topic_costs = []
    if harness.JOBS > 1 and len(run_now) > 1:
        topic_costs = _run_topics_parallel(
            [slug for slug in TOPICS if slug in run_now], harness, harness.JOBS)
    else:
        for slug in TOPICS:
            if slug in run_now:
                checks_before = len(harness.CHECKS_RUN)
                started_at = time.time()
                _run_topic(slug, harness)
                topic_costs.append((slug, time.time() - started_at,
                                    len(harness.CHECKS_RUN) - checks_before))

    print("=" * 72)
    print("%d checks, %d failures, %.0fs%s"
          % (len(harness.CHECKS_RUN), len(harness.FAILURES),
             sum(elapsed for _, elapsed in harness.CHECKS_RUN),
             ("   (%d slow checks skipped: run with --slow)" % len(harness.SKIPPED))
             if harness.SKIPPED else ""))
    if skipped_slow_topics:
        # Same spirit as the skipped-CHECK line above: say plainly that this
        # was not the full suite, how many topics were left out, which ones,
        # and the exact flag that runs them, so nobody mistakes a fast run
        # for a full one.
        print("%d topic(s) skipped (slow): %s - run with --slow, or name one "
              "with --only to run it anyway"
              % (len(skipped_slow_topics), ", ".join(skipped_slow_topics)))
    slowest_checks = sorted(harness.CHECKS_RUN,
                            key=lambda row: -row[1])[:5]
    if slowest_checks and slowest_checks[0][1] >= 5.0:
        print("slowest:")
        for check_name, seconds in slowest_checks:
            if seconds >= 5.0:
                print("   %5.0fs  %s" % (seconds, check_name))
    if "--timing" in argv:
        _print_topic_timing(topic_costs)
    for failure in harness.FAILURES:
        print("   FAILED:", failure)
    print("subprocess spawns: %d calls, %.0fs waiting on child processes"
          % (harness._SUBPROC_CALLS[0], harness._SUBPROC_TIME[0]))
    if harness._PROFILE_OUT:
        with open(harness._PROFILE_OUT, "w") as _pf:
            json.dump({"checks": harness.CHECKS_RUN,
                       # Same figures --timing prints, so a profile run is
                       # readable by a script rather than only by eye.
                       "topics": topic_costs,
                       "subproc_time": harness._SUBPROC_TIME[0],
                       "subproc_calls": harness._SUBPROC_CALLS[0],
                       "total_wall": sum(elapsed for _, elapsed in harness.CHECKS_RUN)}, _pf)
    return 1 if harness.FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
