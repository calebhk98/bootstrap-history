"""Runner for the split regression suite.

`python3 -m sim.tests` runs the quick tier: every sim/tests/test_*.py topic whose file sets a
module-level `QUICK_TOPIC = True`. `--slow` runs every topic (the full suite) and every
slow_check. Topics are discovered from disk (nothing is registered) and run in sorted order.
`--only economy,labour` (comma-separated topic names, as `--list` prints them) runs just those
modules whatever their tier. `--list` prints the topic names and exits.

A topic belongs in the quick tier when it runs in well under a second inside an already
started process: it tests functions or small fixtures, not a whole game over years. New topics
start outside it, so the quick run stays quick by default.

`--timing` adds a per-topic table to the summary: wall seconds, share of the run, and how many
checks each topic bought. It changes nothing about which checks run.

`--jobs N` (default: available cores; `--jobs 1` is the plain sequential run in this process)
runs topics in fresh worker processes, N at a time. Quick topics share N workers between them,
because starting a process costs more than a quick topic; every other topic gets its own. The
runner prints topics in sorted order, so the output is the same as `--jobs 1` apart from
timings. Workers run with `--jobs 1` inside, so in-topic subprocess parallelism does not
multiply with topic parallelism, and each gets its own scratch directories. A topic that must
not run beside others sets a module-level `SERIAL_TOPIC = True`; those run one at a time after
the parallel batch. Per-topic times are remembered in `.cache/` so the next run starts the
longest work first.
"""
import contextlib
import importlib
import io
import json
import os
import random
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import unittest
from concurrent.futures import ThreadPoolExecutor

# So `python3 sim/tests/__main__.py` (run as a plain script, no package
# context) works exactly like `python3 -m sim.tests`: put the repo root on
# sys.path and import everything below by its absolute dotted name, never
# relatively, so it does not matter whether this module itself was reached
# via -m or via this file's own __main__ guard.
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

from sim import cache_root
from sim.tests import machine_slots
from sim.tests.discovery import discover_topics  # noqa: E402

# Every sim/tests/test_*.py is a topic, in sorted order (see discovery.py).
TOPICS = discover_topics()


def _run_topic(slug, harness):
    """Import one topic module, and run it whichever style it is written in.

    Almost every topic module is plain top-level code calling check() at import
    time, so importing it IS running it. One - tierless_schema - is written as
    unittest.TestCase classes instead, which import cleanly and then do
    nothing. It sat in sim/tests/ unregistered and unrun for its whole life,
    and it could not have run even if registered: it imported the tree
    merge, which needed the repository root on sys.path, which is exactly
    what the old `rome.sim.tests` rooting did not provide.

    Rather than rewrite six working tests into the other style, the runner
    accepts both. Each TestCase method becomes one check, so a unittest topic
    reports in the same summary, the same count, and the same exit code as
    every other topic.
    """
    mod = importlib.import_module("sim.tests.test_%s" % slug)

    # Only the module's own classes: a TestCase imported from another topic is that topic's to run.
    loader = unittest.TestLoader()
    own_classes = [getattr(mod, name) for name in dir(mod)
                   if isinstance(getattr(mod, name), type) and issubclass(getattr(mod, name), unittest.TestCase)
                   and getattr(mod, name).__module__ == mod.__name__]
    cases = unittest.TestSuite(loader.loadTestsFromTestCase(test_class) for test_class in own_classes)
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

    Three columns: wall seconds, share of the measured total, and how many checks that bought.
    It is the evidence for which tier a topic belongs in.

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


_TIMES_FILE = os.path.join(cache_root.cache_root(), "test_topic_seconds.json")


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


def _worker_main(slugs, result_path):
    """Run topics one after another in this (fresh) process and dump each one's results as JSON.

    Each topic's printed output is captured on its own, and a topic that raises is recorded as
    crashed without stopping the ones after it. The file is rewritten after every topic, so a
    process that dies outright still leaves the finished topics' results."""
    from sim.tests import harness
    results = {}
    for slug in slugs:
        checks_before, failures_before = len(harness.CHECKS_RUN), len(harness.FAILURES)
        skipped_before = len(harness.SKIPPED)
        subprocess_time_before = harness._SUBPROC_TIME[0]
        subprocess_calls_before = harness._SUBPROC_CALLS[0]
        output = io.StringIO()
        crash = None
        started_at = time.time()
        with contextlib.redirect_stdout(output):
            try:
                _run_topic(slug, harness)
            except (Exception, SystemExit):
                crash = traceback.format_exc()
        results[slug] = {"seconds": time.time() - started_at,
                         "stdout": output.getvalue(),
                         "crash": crash,
                         "checks": harness.CHECKS_RUN[checks_before:],
                         "failures": harness.FAILURES[failures_before:],
                         "skipped": harness.SKIPPED[skipped_before:],
                         "subproc_time": harness._SUBPROC_TIME[0] - subprocess_time_before,
                         "subproc_calls": harness._SUBPROC_CALLS[0] - subprocess_calls_before}
        with open(result_path, "w", encoding="utf-8") as handle:
            json.dump(results, handle)
    return 0


def _start_worker(slugs, harness, result_dir, tag):
    """Launch a fresh process for a list of topics; in-topic parallelism is 1 per worker."""
    result_path = os.path.join(result_dir, tag + ".json")
    command = [sys.executable, os.path.abspath(__file__), "--worker", ",".join(slugs),
               "--worker-result", result_path, "--worker-tag", tag, "--jobs", "1"]
    if harness.SLOW:
        command.append("--slow")
    completed = harness._real_subprocess_run(command, capture_output=True, text=True,
                                             cwd=_REPO_ROOT)
    results = {}
    try:
        with open(result_path, encoding="utf-8") as handle:
            results = json.load(handle)
    except (OSError, ValueError):
        pass
    return completed, results


def _quick_batches(slugs, seconds_before, count):
    """Quick topics shared out over `count` workers, longest first onto the least loaded."""
    batches = [[] for _ in range(max(1, min(count, len(slugs))))]
    loads = [0.0] * len(batches)
    for slug in sorted(slugs, key=lambda slug: -seconds_before.get(slug, 0.0)):
        lightest = loads.index(min(loads))
        batches[lightest].append(slug)
        loads[lightest] += seconds_before.get(slug, 0.0)
    return [batch for batch in batches if batch]


def _report_progress(slugs, results, progress):
    """One stderr line per finished topic as it finishes, and its time remembered at once, so a
    long run shows where it is and an interrupted one still leaves its timings."""
    with progress["lock"]:
        for slug in slugs:
            progress["done"] += 1
            result = results.get(slug)
            if result is None:
                state = "crashed"
            else:
                state = "%.1fs%s" % (result["seconds"],
                                     " FAIL" if result["failures"] or result["crash"] else "")
            sys.stderr.write("  [%d/%d] %s %s\n" % (progress["done"], progress["total"], slug, state))
        sys.stderr.flush()
        _save_topic_seconds([(slug, results[slug]["seconds"], 0) for slug in slugs if slug in results])


def _fork_topics(slugs, harness, result_dir, held_slots=()):
    """Run topics in a child forked from this warmed process; returns the child's pid and files.

    The child starts with everything this process has already imported, loaded and built,
    and changes nothing here: its writes are its own copy."""
    tag = slugs[0] if len(slugs) == 1 else "batch_" + slugs[0]
    result_path = os.path.join(result_dir, tag + ".json")
    error_path = os.path.join(result_dir, tag + ".stderr")
    pid = os.fork()
    if pid:
        return pid, result_path, error_path
    status = 1
    for slot in held_slots:     # the parent holds the slots; a copy here would keep them past their worker
        machine_slots.release(slot)
    os.environ[machine_slots.INSIDE_SLOT_ENV] = "1"
    try:
        error_handle = os.open(error_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.dup2(error_handle, 2)
        null_handle = os.open(os.devnull, os.O_WRONLY)
        os.dup2(null_handle, 1)
        random.seed()
        harness._LAST_AT = time.time()
        harness.JOBS = 1
        harness.use_scratch_tag(tag)
        status = _worker_main(slugs, result_path)
        harness._remove_scratch_dirs_if_green()
    except BaseException:
        traceback.print_exc()
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(status)


def _run_topics_forked(run_now, harness, jobs):
    """Run topics in children forked from this process, `jobs` at a time: each other topic in a
    child of its own, the quick ones shared out over a few."""
    harness.sim()       # warm what every game build shares before the first fork
    seconds_before = _load_topic_seconds()
    known = sorted(seconds_before.values())
    unknown_guess = known[len(known) // 2] if known else 0.0
    quick = set(harness.QUICK_TOPICS)
    pending = [[slug] for slug in run_now if slug not in quick]
    pending += _quick_batches([slug for slug in run_now if slug in quick], seconds_before, jobs)
    pending.sort(key=lambda slugs: -sum(seconds_before.get(slug, unknown_guess) for slug in slugs))
    progress = {"done": 0, "total": len(run_now), "lock": threading.Lock()}
    outcomes, running = {}, {}
    with tempfile.TemporaryDirectory(prefix="rome_suite_") as result_dir:
        while pending or running:
            while pending and len(running) < jobs:
                # Workers draw on the machine's slot pool; while ours are running, reap rather than wait.
                slot = machine_slots.acquire(wait=not running)
                if slot is False:
                    break
                slugs = pending.pop(0)
                pid, result_path, error_path = _fork_topics(
                    slugs, harness, result_dir, [entry[3] for entry in running.values()])
                running[pid] = (slugs, result_path, error_path, slot)
            pid, wait_status = os.wait()
            if pid not in running:
                continue
            slugs, result_path, error_path, slot = running.pop(pid)
            machine_slots.release(slot)
            results = {}
            try:
                with open(result_path, encoding="utf-8") as handle:
                    results = json.load(handle)
            except (OSError, ValueError):
                pass
            try:
                with open(error_path, encoding="utf-8", errors="replace") as handle:
                    error_text = handle.read()
            except OSError:
                error_text = ""
            completed = subprocess.CompletedProcess(slugs, os.waitstatus_to_exitcode(wait_status),
                                                    "", error_text)
            _report_progress(slugs, results, progress)
            for slug in slugs:
                outcomes[slug] = (completed, results.get(slug))
    return _merge_outcomes(run_now, outcomes, harness)


def _run_topics_parallel(run_now, harness, jobs):
    """Run topics in worker processes; print and merge results in topic order.

    Quick topics share a few processes, since starting one costs more than the topic itself;
    every other topic gets a fresh process of its own."""
    serial = set(harness.SERIAL_TOPICS)
    quick = set(harness.QUICK_TOPICS)
    seconds_before = _load_topic_seconds()
    work = [[slug] for slug in run_now if slug not in serial and slug not in quick]
    work += _quick_batches([slug for slug in run_now if slug in quick and slug not in serial],
                           seconds_before, jobs)
    work.sort(key=lambda slugs: -sum(seconds_before.get(slug, 0.0) for slug in slugs))
    serial_work = [[slug] for slug in run_now if slug in serial]
    topic_costs = []
    outcomes = {}
    progress = {"done": 0, "total": len(run_now), "lock": threading.Lock()}
    with tempfile.TemporaryDirectory(prefix="rome_suite_") as result_dir:
        def run(slugs):
            tag = slugs[0] if len(slugs) == 1 else "batch_" + slugs[0]
            completed, results = _start_worker(slugs, harness, result_dir, tag)
            _report_progress(slugs, results, progress)
            return completed, results
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = [(slugs, pool.submit(run, slugs)) for slugs in work]
            # Serial topics wait for the whole parallel batch, then run one at a time.
            for _, future in futures:
                future.exception()
        finished = [(slugs, future.result()) for slugs, future in futures]
        finished += [(slugs, run(slugs)) for slugs in serial_work]
        for slugs, (completed, results) in finished:
            for slug in slugs:
                outcomes[slug] = (completed, results.get(slug))
    return _merge_outcomes(run_now, outcomes, harness)


def _merge_outcomes(run_now, outcomes, harness):
    """Print each topic's output in topic order and fold its results into the harness totals."""
    topic_costs = []
    for slug in run_now:
        completed, result = outcomes[slug]
        if result is None:
            message = "%s: worker crashed (exit %s)" % (slug, completed.returncode)
            print("  %-58s FAIL %s" % (message, completed.stderr.strip()[-400:]))
            harness.CHECKS_RUN.append((message, 0.0))
            harness.FAILURES.append(message)
            topic_costs.append((slug, 0.0, 1))
            continue
        sys.stdout.write(result["stdout"])
        harness.CHECKS_RUN.extend((name, took) for name, took in result["checks"])
        harness.FAILURES.extend(result["failures"])
        harness.SKIPPED.extend(result["skipped"])
        harness._SUBPROC_TIME[0] += result["subproc_time"]
        harness._SUBPROC_CALLS[0] += result["subproc_calls"]
        if result["crash"]:
            message = "%s: worker crashed (exception)" % slug
            print("  %-58s FAIL %s" % (message, result["crash"].strip()[-400:]))
            harness.CHECKS_RUN.append((message, 0.0))
            harness.FAILURES.append(message)
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
        return _worker_main(argv[position + 1].split(","), result_path)

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
    # same way whether reached via -m or via this file's own __main__ guard.
    from sim.tests import harness

    # The default run is the quick tier: topics whose file sets QUICK_TOPIC = True. --slow (or
    # ROME_SLOW_TESTS) runs every topic. A topic named with --only runs whatever its tier.
    skipped_slow_topics = ([slug for slug in selected
                             if slug not in harness.QUICK_TOPICS] if only is None and not harness.SLOW
                            else [])
    run_now = [slug for slug in selected if slug not in skipped_slow_topics]

    print("PLAYTEST REGRESSIONS\n" + "=" * 72)
    # Per-topic wall time is measured here (check() only times single checks); --timing prints it.
    topic_costs = []
    if harness.JOBS > 1 and len(run_now) > 1 and hasattr(os, "fork"):
        topic_costs = _run_topics_forked(
            [slug for slug in TOPICS if slug in run_now], harness, harness.JOBS)
    elif harness.JOBS > 1 and len(run_now) > 1:
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
        print("quick tier only: %d of %d topics skipped - run with --slow for the full suite, "
              "or name one with --only" % (len(skipped_slow_topics), len(selected)))
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
