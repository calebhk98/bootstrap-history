"""`openings`: open a game of each civilisation and ship the cache entries its opening used
(sim/engine/shipped_openings.py), after the opening checks (sim/engine/opening_checks.py) pass; one that fails
is refused unless `--allow-failing REASON` is given."""
import concurrent.futures
import multiprocessing
import os
import time

from sim.engine import opening_checks_gate, shipped_openings_build
from . import openings_manifest
from sim.engine.ui_port import civilization_ids


def spin_up_line(result):
    """One plain line on how the opening's first stage ended."""
    if not result:
        return "spin-up: no result recorded"
    if result["settled"]:
        return "spin-up: settled after %d years (largest yearly change %.3g)" % (result["years"], result["gap"])
    return ("spin-up: NOT SETTLED after %d years; the opening is wherever the cycle stood "
            "(largest yearly change %.3g)" % (result["years"], result["gap"]))


def build_one(civ_id, allow_failing):
    """(civ id, the entries kept, the spin-up's result, seconds, the refusal or None) of one civilisation's opening."""
    started = time.time()
    gate = opening_checks_gate.OpeningGate(civ_id, allow_failing)
    try:
        entries, spin_up = shipped_openings_build.build_reporting(civ_id, before_writing=gate)
    except SystemExit as refusal:
        return civ_id, [], None, time.time() - started, str(refusal)
    return civ_id, entries + gate.shipped, spin_up, time.time() - started, None


def default_jobs(count):
    """Openings built at once: one per civilisation, up to the machine's cores."""
    return max(1, min(count, os.cpu_count() or 1))


def cmd_openings(args):
    civs = [part.strip() for part in (args.civs or "").split(",") if part.strip()] or civilization_ids()
    jobs = args.jobs or default_jobs(len(civs))
    allow_failing = getattr(args, "allow_failing", None)
    kept, refused = [], []
    if jobs == 1:
        finished = (build_one(civ_id, allow_failing) for civ_id in civs)
    else:
        # each civilisation in a process of its own; the disk cache's per-key lock covers entries two of them share
        pool = concurrent.futures.ProcessPoolExecutor(jobs, mp_context=multiprocessing.get_context("fork"))
        finished = (future.result() for future in concurrent.futures.as_completed(
            [pool.submit(build_one, civ_id, allow_failing) for civ_id in civs]))
    for civ_id, entries, spin_up, seconds, refusal in finished:
        if refusal is not None:
            refused.append(civ_id)
            print(refusal, flush=True)
            continue
        kept.extend(entries)
        openings_manifest.record([civ_id], openings_manifest.current_digest())
        print("%s: shipped %d cache entries (%.0fs)" % (civ_id, len(entries), seconds), flush=True)
        print("  %s" % spin_up_line(spin_up), flush=True)
    if refused:
        print("not shipped: %s; nothing pruned" % ", ".join(refused), flush=True)
        return 1
    if args.prune:
        for namespace, key in shipped_openings_build.prune(kept):
            print("removed stale %s/%s" % (namespace, key))
    return 0
