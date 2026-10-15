"""The retirement rule for promise-kind declarations (Complaints/closed/509).

A `temporary_heuristic` (or `hardcoded_outcome`) declared after the recorded baseline must name, in
`retire`, the complaint or mechanism that will replace it. The baseline is the sorted names of the
promises that predate the rule; it only shrinks.

    python3 sim/constants.py --record-baseline    rewrite the baseline from the current registry
    python3 sim/constants.py --prune-baseline     drop baseline names that are no longer declared
    python3 sim/constants.py --compare <git ref>  burndown count at that ref against this tree
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

PROMISE_KINDS = ("temporary_heuristic", "hardcoded_outcome")
BASELINE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "data", "review", "heuristic_baseline.txt")
_PLACEHOLDERS = {"todo", "tbd", "none", "n/a", "later", "unknown", "?"}


def promise_names(registry):
    """Names of every declared promise, sorted."""
    return sorted(name for name, entry in registry.items() if entry["kind"] in PROMISE_KINDS)


def read_baseline(path=BASELINE_PATH):
    with open(path, encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def write_baseline(names, path=BASELINE_PATH):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("".join(name + "\n" for name in sorted(set(names))))


def has_retirement(entry):
    retire = (entry.get("retire") or "").strip().lower()
    return bool(retire) and retire not in _PLACEHOLDERS


def missing_retirement(registry, baseline):
    """Promises outside the baseline that name no retirement."""
    known = set(baseline)
    return [name for name in promise_names(registry)
            if name not in known and not has_retirement(registry[name])]


def stale_baseline(registry, baseline):
    """Baseline names that are no longer declared as a promise."""
    current = set(promise_names(registry))
    return [name for name in baseline if name not in current]


def counts(registry):
    heuristics = [entry for entry in registry.values() if entry["kind"] == "temporary_heuristic"]
    return {"temporary_heuristics": len(heuristics),
            "with_retire": sum(1 for entry in heuristics if has_retirement(entry))}


_COUNT_LINE = re.compile(r"(\d+) numbers declared, (\d+) are temporary heuristics")
_RETIRE_LINE = re.compile(r"(\d+) of the temporary heuristics name a retirement")


def burndown_at(repository_root):
    """(temporary heuristic count, count naming a retirement or None) from a tree's --burndown."""
    run = subprocess.run([sys.executable, os.path.join("sim", "constants.py"), "--burndown"],
                         cwd=repository_root, capture_output=True, text=True, check=False)
    count = _COUNT_LINE.search(run.stdout)
    if not count:
        raise RuntimeError("no burndown count in output of that tree:\n" + run.stderr[-400:])
    retire = _RETIRE_LINE.search(run.stdout)
    return int(count.group(2)), (int(retire.group(1)) if retire else None)


def compare(ref, repository_root, current):
    """Print the heuristic count at `ref` beside this tree's, and the difference."""
    scratch = tempfile.mkdtemp(prefix="burndown_compare_")
    try:
        archive = subprocess.run(["git", "archive", ref], cwd=repository_root,
                                 capture_output=True, check=False)
        if archive.returncode:
            raise RuntimeError("git archive %s failed: %s" % (ref, archive.stderr.decode()[-300:]))
        subprocess.run(["tar", "-x", "-C", scratch], input=archive.stdout, check=True)
        before, before_retire = burndown_at(scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    after = current["temporary_heuristics"]
    print("temporary heuristics at %s: %d" % (ref, before))
    print("temporary heuristics now: %d (%+d)" % (after, after - before))
    if before_retire is not None:
        print("naming a retirement at %s: %d, now: %d (%+d)" % (
            ref, before_retire, current["with_retire"], current["with_retire"] - before_retire))
