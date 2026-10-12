"""`openings`: run each civilisation's full spin-up and ship the result (sim/engine/shipped_openings.py)."""
import time

from sim.engine import shipped_openings_build
from sim.engine.ui_port import civilization_ids


def cmd_openings(args):
    civs = [part.strip() for part in (args.civs or "").split(",") if part.strip()] or civilization_ids()
    keys = []
    for civ_id in civs:
        started = time.time()
        key = shipped_openings_build.build(civ_id)
        keys.append(key)
        print("%s: shipped %s (%.0fs)" % (civ_id, key, time.time() - started), flush=True)
    if args.prune:
        for key in shipped_openings_build.prune(keys):
            print("removed stale %s" % key)
    return 0
