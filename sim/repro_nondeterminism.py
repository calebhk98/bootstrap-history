#!/usr/bin/env python3
"""The same simulation, run twice in one process, gives two different answers.

    python3 sim/repro_nondeterminism.py           the ten-second repro
    python3 sim/repro_nondeterminism.py --bisect  find the year and the field
    python3 sim/repro_nondeterminism.py --caches  what is shared between runs

WHAT THIS IS. `perf_fingerprint.py` is the tool `sim/ARCHITECTURE.md` names as
the way to prove a change altered nothing. It does not reproduce its own
recording. A pristine checkout, recorded and then checked against itself,
reports two of nine scenarios diverged; two recordings of it diverge in one of
nine, at a different scenario and a different year each time.

Twenty minutes a run and never the same failure twice is not a bug you can
debug. This script is the same bug in about ten seconds. One scenario, run
four times in one process, same seed, no changes in between:

    run 1  7d77685af3129077        run 1  d35355f9c94e35a8
    run 2  d35355f9c94e35a8        run 2  d35355f9c94e35a8
    run 3  d35355f9c94e35a8        run 3  7de0c8b0741215f5
    run 4  d35355f9c94e35a8        run 4  d35355f9c94e35a8

Two invocations of this script, minutes apart. WHICH run is the odd one out
changes; that there is one is reliable. So this is not a cold-cache effect -
an early guess, recorded here because it is the obvious wrong answer and
somebody else will have it too. It is sporadic, which points at something
sensitive to the memory allocator rather than to run order.

WHAT IT LOOKS LIKE WHEN IT BITES. `--bisect` walks the two runs year by year.
On rome_100ad/seed1 the first difference is at year index 18, in one field of
one project:

    potash_soda  ph_left   A=152.51383869514427  B=152.51383869514555

A difference of 1.3e-12, in the last bits of a float, which is the signature of
the same sum taken in a different ORDER. `economy.done_in_order()`'s own
docstring describes this exact failure and the damage it does:

    "floating point addition is not associative, so the totals differed in
     their last bits between one process and the next. Over five hundred years
     those last bits decide which side of a threshold you land on, and the
     same --seed gave two different answers on alternate invocations."

That was fixed in three places. This is a fourth, somewhere else.

WHAT IS RULED OUT. Recorded so nobody repeats it:

  * Hash-seed randomisation. One scenario alone in a fresh process gives a
    byte-identical digest over three runs with PYTHONHASHSEED unset and three
    with it fixed at 0.
  * Mutation of the shared tree. NODES and ORDER hash identically before and
    after six scenarios run against them.
  * Mutation of any module-level container in data, economy, labour, projects,
    society, geography, fog, commodities or proto.nodes. None changes content.
  * The CommodityLedger accumulating state. It is read-only in practice: none
    of its four attributes changes across a 60-year run.
  * The id()-keyed cache in _revenue_upkeep_candidates. This looked like the
    answer - id() is an address, a freed object's address is reusable, and
    proto/nodes.py documents that exact hazard and defends against it while
    the other three id()-keyed caches do not. A probe recomputing the true
    answer every call found 0 stale answers in 64,157 calls.
  * The id()-keyed _demand_by_tag_cache, for a duller reason: it hits three
    times in four 80-year runs. It is not a hot enough path to matter.

WHAT IS LEFT. `--caches` shows the only cross-Sim state found so far: three
caches on EconomyMixin, None before the first run and shared by every Sim in
the process afterwards. Clearing them between runs DOES change the answer, so
they are implicated. But they are built deterministically from JSON in file
order and never mutated, so they cannot be changing a sum directly - the
likeliest reading is that constructing them perturbs allocation, and something
else downstream is sensitive to that. Which is another way of saying there is
still an order-dependent float sum in here that nobody has found.

Find it, fix it by making the order deterministic (sort, or iterate a list),
and turn this script into a regression check in sim/tests/.
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import perf_fingerprint as P
from engine.economy import EconomyMixin

SHARED_CACHES = ("_commod_ledger_cache", "_material_commod_map_cache",
                 "_material_prices_cache")


def repro(runs=4):
    """The headline: run one scenario several times, print the digests."""
    scenario = P.SCENARIOS[0]
    print("%s, run %d times in ONE process:\n" % (P.name_of(scenario), runs))
    digests = []
    for i in range(runs):
        years, _cpu, _ = P.run(scenario)
        digest = P.digest(years)
        digests.append(digest)
        print("  run %d  %s" % (i + 1, digest))
    print()
    if len(set(digests)) == 1:
        print("All %d runs agree. That happens: the effect is sporadic, not" % runs)
        print("every invocation trips it. Raise --runs before concluding it is")
        print("fixed; %d runs is enough to see it most of the time, not always."
              % runs)
        return 0
    print("DIVERGED: %d distinct answers from %d runs of the same scenario,"
          % (len(set(digests)), runs))
    print("same seed, one process, nothing changed in between. Any run can be")
    print("the odd one out. perf_fingerprint records one of these and checks")
    print("against another, so it accuses changes that were never made.")
    return 1


def bisect(attempts=8):
    """Which year, which field, and by how much.

    Runs until two runs actually disagree, because they often do not - see
    the note on sporadic behaviour above. Keeping every year's full state for
    two runs at a time, rather than for all of them, keeps the memory down.
    """
    scenario = P.SCENARIOS[0]
    first_years, _, first_states = P.run(scenario, keep_states=True)
    diff_index = None
    for attempt in range(attempts):
        second_years, _, second_states = P.run(scenario, keep_states=True)
        diff_index = next((position for position, (first_year_value, second_year_value)
                           in enumerate(zip(first_years, second_years))
                           if first_year_value != second_year_value), None)
        if diff_index is not None:
            print("(disagreed on attempt %d)" % (attempt + 2))
            break
    if diff_index is None:
        print("%d runs all agreed; nothing to bisect this time. Try again."
              % (attempts + 1))
        return 0
    print("first differing year index: %d\n" % diff_index)
    first_state, second_state = first_states[diff_index], second_states[diff_index]
    for field in sorted(set(first_state) | set(second_state)):
        if first_state.get(field) == second_state.get(field):
            continue
        first_value, second_value = first_state.get(field), second_state.get(field)
        if isinstance(first_value, dict) and isinstance(second_value, dict):
            for key in sorted(set(first_value) | set(second_value)):
                first_entry, second_entry = first_value.get(key) or {}, second_value.get(key) or {}
                if not (isinstance(first_entry, dict) and isinstance(second_entry, dict)):
                    if first_entry != second_entry:
                        print("  %-14s %-22s A=%s B=%s"
                              % (field, key, first_entry, second_entry))
                    continue
                for subfield in sorted(set(first_entry) | set(second_entry)):
                    if first_entry.get(subfield) != second_entry.get(subfield):
                        print("  %-14s %-22s %-22s\n%17sA=%s\n%17sB=%s"
                              % (field, key, subfield, "", first_entry.get(subfield), "", second_entry.get(subfield)))
        else:
            print("  %-14s A=%s\n%17sB=%s"
                  % (field, repr(first_value)[:90], "", repr(second_value)[:90]))
    return 1


def _hash_of(value):
    try:
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:10]
    except Exception:
        return "unhashable"


def caches():
    """What is shared between one run and the next."""
    print("EconomyMixin caches, before and after one run:\n")
    for name in SHARED_CACHES:
        print("  %-32s %s" % (name, getattr(EconomyMixin, name, None)))
    P.run(dict(P.SCENARIOS[0], years=20))
    print()
    for name in SHARED_CACHES:
        value = getattr(EconomyMixin, name, None)
        print("  %-32s %s" % (name, "populated, hash " + _hash_of(vars(value) if hasattr(value, "__dict__") else value)))
    print()
    print("These are cached ON THE CLASS, so every Sim built afterwards in this")
    print("process shares them. They are built deterministically from JSON and")
    print("never mutated - checked - yet clearing them between runs changes the")
    print("result, which is the loose end.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bisect", action="store_true",
                    help="find the first differing year and field")
    parser.add_argument("--caches", action="store_true",
                    help="show the state shared between runs")
    parser.add_argument("--runs", type=int, default=4)
    args = parser.parse_args(argv)
    if args.bisect:
        return bisect()
    if args.caches:
        return caches()
    return repro(args.runs)


if __name__ == "__main__":
    sys.exit(main())
