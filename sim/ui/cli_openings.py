"""`openings`: open a game of each civilisation and ship the cache entries its opening used
(sim/engine/shipped_openings.py)."""
import time

from sim.engine import shipped_openings_build
from sim.engine.ui_port import civilization_ids


def spin_up_line(result):
    """One plain line on how the opening's first stage ended."""
    if not result:
        return "spin-up: no result recorded"
    if result["settled"]:
        return "spin-up: settled after %d years (largest yearly change %.3g)" % (result["years"], result["gap"])
    return ("spin-up: NOT SETTLED after %d years; the opening is wherever the cycle stood "
            "(largest yearly change %.3g)" % (result["years"], result["gap"]))


def cmd_openings(args):
    civs = [part.strip() for part in (args.civs or "").split(",") if part.strip()] or civilization_ids()
    kept = []
    for civ_id in civs:
        started = time.time()
        entries, spin_up = shipped_openings_build.build_reporting(civ_id)
        kept.extend(entries)
        print("%s: shipped %d cache entries (%.0fs)" % (civ_id, len(entries), time.time() - started), flush=True)
        print("  %s" % spin_up_line(spin_up), flush=True)
    if args.prune:
        for namespace, key in shipped_openings_build.prune(kept):
            print("removed stale %s/%s" % (namespace, key))
    return 0
