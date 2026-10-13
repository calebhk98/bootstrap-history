"""`openings`: open a game of each civilisation and ship the cache entries its opening used
(sim/engine/shipped_openings.py)."""
import time

from sim.engine import shipped_openings_build
from sim.engine.ui_port import civilization_ids


def cmd_openings(args):
    civs = [part.strip() for part in (args.civs or "").split(",") if part.strip()] or civilization_ids()
    kept = []
    for civ_id in civs:
        started = time.time()
        entries = shipped_openings_build.build(civ_id)
        kept.extend(entries)
        print("%s: shipped %d cache entries (%.0fs)" % (civ_id, len(entries), time.time() - started), flush=True)
    if args.prune:
        for namespace, key in shipped_openings_build.prune(kept):
            print("removed stale %s/%s" % (namespace, key))
    return 0
