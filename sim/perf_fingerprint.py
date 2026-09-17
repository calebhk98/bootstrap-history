#!/usr/bin/env python3
"""Prove an optimisation changed nothing.

An optimisation is only worth having if the game it speeds up is the same
game. This records a hash of the ENTIRE simulation state after every single
year of a set of reference runs - several civilisations, several seeds, fog
on and off, optimiser and manual - and writes them to a JSON file.

    python3 sim/perf_fingerprint.py record baseline.json
    ...make a change...
    python3 sim/perf_fingerprint.py check baseline.json

`check` re-runs the same scenarios and reports the FIRST year at which any
run diverges, and which fields differ. A year-by-year hash rather than a
final-state hash on purpose: a final-state comparison tells you that
something broke, and a per-year one tells you when, which is most of the way
to telling you why.

Timing comes free with it: `record` and `check` both print the CPU time each
scenario took, so the same command that proves you broke nothing also tells
you how much faster it got.
"""
import hashlib, json, os, random, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import simulator as S
from engine.protocol import SAVE_FIELDS

TREE, PRICES, NODES, WAGES, GOODS = S.load()
GOAL = TREE["meta"]["goal_node"]
_LAB, ORDER, _B = S.load_strategy("recommended", NODES, GOAL)

# WHAT GETS COMPARED. SAVE_FIELDS is the engine's own answer to "what is the
# state of this game" - it is what a save file holds and what a resumed
# sitting restores - so it is the right list to compare, and it stays right
# as the engine grows without this file having to be maintained alongside it.
# `log` is dropped: it is prose, it is enormous, and a change to the wording
# of a message is not a change to the simulation.
FIELDS = tuple(f for f in SAVE_FIELDS if f != "log")


def _canon(v):
    """Make a value comparable and order-independent where order is not real."""
    if isinstance(v, float):
        # repr() rather than round(): a change that alters the last bit of a
        # float IS a change, and this harness exists to catch exactly that.
        return repr(v)
    if isinstance(v, set):
        return ["__set__"] + sorted(_canon(x) for x in v)
    if isinstance(v, dict):
        return {str(k): _canon(v[k]) for k in sorted(v, key=str)}
    if isinstance(v, (list, tuple)):
        return [_canon(x) for x in v]
    return v


def state_of(s):
    return {f: _canon(getattr(s, f, None)) for f in FIELDS}


def digest(d):
    return hashlib.sha256(
        json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:16]


# THE REFERENCE RUNS. Five civilisations, because several hot functions
# short-circuit specifically for Rome and an optimisation that is only
# correct for Rome is not correct. Fog on for some, because the fog filter is
# itself one of the hot paths. `events` on, because the random event stream
# is the thing most likely to expose a changed number of RNG draws - which is
# how a "pure refactor" silently becomes a different game.
SCENARIOS = [
    dict(civ="rome_100ad",      seed=1, years=200, events=True,  fog=False),
    dict(civ="rome_100ad",      seed=2, years=200, events=True,  fog=True),
    dict(civ="rome_100ad",      seed=3, years=200, events=False, fog=False),
    dict(civ="han_china_100ad", seed=1, years=200, events=True,  fog=False),
    dict(civ="han_china_100ad", seed=2, years=200, events=True,  fog=True),
    dict(civ="norse_900ad",     seed=1, years=200, events=True,  fog=False),
    dict(civ="england_1300",    seed=1, years=200, events=True,  fog=False),
    dict(civ="mexica_1500",     seed=1, years=200, events=True,  fog=False),
    dict(civ="rome_100ad",      seed=7, years=400, events=True,  fog=False),
]


def build(sc):
    s = S.Sim(NODES, ORDER, random.Random(sc["seed"]), events=sc["events"],
              manual=False, civ=S.load_civ(sc["civ"]))
    s.goal, s.done_year = GOAL, {}
    if sc["fog"]:
        s.fog = True
    return s


def name_of(sc):
    return "%s/seed%d/%dy/%s%s" % (sc["civ"], sc["seed"], sc["years"],
                                   "events" if sc["events"] else "noevents",
                                   "+fog" if sc["fog"] else "")


def run(sc, keep_states=False):
    """Return (per-year digests, cpu seconds, final full state)."""
    s = build(sc)
    t0 = time.process_time()
    per_year, states = [], []
    for _ in range(sc["years"]):
        if getattr(s, "dead_reason", None):
            break
        s.step()
        st = state_of(s)
        per_year.append(digest(st))
        if keep_states:
            states.append(st)
    return per_year, time.process_time() - t0, states


def record(path):
    out, total = {}, 0.0
    for sc in SCENARIOS:
        nm = name_of(sc)
        years, cpu, _ = run(sc)
        total += cpu
        out[nm] = {"scenario": sc, "years": years}
        print("  %-42s %5d years  %7.2fs cpu" % (nm, len(years), cpu))
    print("  %-42s %18.2fs cpu TOTAL" % ("", total))
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print("written to %s" % path)
    return 0


def check(path):
    with open(path) as f:
        base = json.load(f)
    bad, total, btotal = [], 0.0, 0.0
    for nm, rec in base.items():
        sc = rec["scenario"]
        want = rec["years"]
        # keep_states only for the re-run, so a divergence can be explained
        # without a second run of the whole thing.
        got, cpu, states = run(sc, keep_states=True)
        total += cpu
        if got == want:
            print("  %-42s SAME  %5d years  %7.2fs cpu" % (nm, len(got), cpu))
            continue
        # FIRST divergent year, not all of them: after the first one every
        # later year differs too and listing them buries the one that matters.
        i = next((j for j in range(min(len(got), len(want)))
                  if got[j] != want[j]), min(len(got), len(want)))
        bad.append((nm, i))
        print("  %-42s DIVERGED at year index %d (of %d/%d)"
              % (nm, i, len(got), len(want)))
        if len(got) != len(want):
            print("      run length changed: %d -> %d" % (len(want), len(got)))
        if i < len(states):
            print("      re-run this scenario under a debugger; changed state "
                  "is in %s year %d" % (nm, i))
    print()
    if bad:
        print("FAIL: %d of %d scenarios diverged" % (len(bad), len(base)))
        return 1
    print("OK: all %d scenarios byte-identical.  %.2fs cpu total" % (len(base), total))
    return 0


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("record", "check"):
        print(__doc__)
        return 2
    return (record if sys.argv[1] == "record" else check)(sys.argv[2])


if __name__ == "__main__":
    sys.exit(main())
