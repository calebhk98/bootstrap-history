"""The price-solve cache and the warm start of an in-game solve, called on stand-ins. `solve_cache.cached_json` computes on a miss,
reads on a hit, recomputes when the cache directory is gone and still answers when the directory cannot be written, cold and warm
alike. `solved_prices_at_wages` solves a rate away from the starting one starting from the solve at the starting rate (itself
started cold), so its answer depends on its own inputs only. The solver is replaced by a recorder, the production catalogue by a
small one."""

QUICK_TOPIC = True

import os
import shutil
import tempfile
from unittest import mock

from .harness import check

from sim.engine import prices, solve_cache

# ---- cached_json
directory = tempfile.mkdtemp(prefix="solve_cache_rule_")
calls = []


def compute():
    calls.append(1)
    return {"prices": {"iron": 1.5}, "count": len(calls) * 0 + 7}


try:
    with mock.patch.object(solve_cache.shipped_openings, "read", return_value=None):
        cold = solve_cache.cached_json("key_a", compute, directory)
        warm = solve_cache.cached_json("key_a", compute, directory)
        check("a miss computes once and a hit does not compute again", len(calls) == 1, calls)
        check("cold and warm give the same value", cold == warm == {"prices": {"iron": 1.5}, "count": 7}, (cold, warm))
        other = solve_cache.cached_json("key_b", compute, directory)
        check("another key is its own entry", len(calls) == 2 and other == cold, calls)
        shutil.rmtree(directory)
        recomputed = solve_cache.cached_json("key_a", compute, directory)
        check("with the cache directory deleted the value is computed again and is the same", len(calls) == 3 and recomputed == cold, calls)

        blocker = os.path.join(tempfile.gettempdir(), "solve_cache_rule_file_%d" % os.getpid())
        with open(blocker, "w") as handle:
            handle.write("x")
        try:
            unwritable = solve_cache.cached_json("key_c", compute, os.path.join(blocker, "sub"))
            check("a cache directory that cannot be written is not required: the value is still returned", unwritable == cold)
        finally:
            os.remove(blocker)
finally:
    shutil.rmtree(directory, ignore_errors=True)

# ---- a shipped entry stands in for the computation
shipped_directory = tempfile.mkdtemp(prefix="solve_cache_shipped_")
computed = []
try:
    with mock.patch.object(solve_cache.shipped_openings, "read", return_value={"prices": {"iron": 9.0}}) as shipped:
        value = solve_cache.cached_json("key_s", lambda: computed.append(1) or {"prices": {}}, shipped_directory)
        check("a miss with an entry shipped for the key reads it and does not compute", value == {"prices": {"iron": 9.0}} and not computed, computed)
        check("the shipped entry is asked for by the cache's name and the key",
              shipped.call_args.args == (os.path.basename(shipped_directory), "key_s"), shipped.call_args)
        check("the shipped entry is kept as the cache's own, so the next read finds it there",
              solve_cache.cached_json("key_s", lambda: computed.append(1), shipped_directory) == value and not computed)
finally:
    shutil.rmtree(shipped_directory, ignore_errors=True)

# ---- warm start
STARTING_RATE = 0.05
CATALOGUE = {}


def solve_json(production_entries, gate_nodes_held, civilization_id, document_ratios, admitted, interest_rate, civilization,
              farmed_hectares, in_game, initial_prices, rent):
    solve_json.calls.append({"rate": interest_rate, "initial": initial_prices, "in_game": in_game})
    return {"prices_in_labour_hours": {"iron": 10.0 * interest_rate + (1.0 if initial_prices else 0.0)},
            "resolvable_materials": ["iron"], "chosen_recipe_by_material": {}, "converged": True, "iterations_run": 3}


def price_at(rate, entries=CATALOGUE):
    """The solve at `rate` over `entries`, in a process whose own catalogue is CATALOGUE."""
    solve_json.calls = []
    prices.reset_caches_for_tests()
    with mock.patch.object(prices, "_DEFAULT_PRODUCTION_ENTRIES", CATALOGUE), \
            mock.patch.object(prices, "_solve_to_json", side_effect=solve_json), \
            mock.patch.object(prices.solve_prices, "load_starting_interest_rate", return_value=STARTING_RATE), \
            mock.patch.object(prices.solve_cache, "solve_key", return_value="key"), \
            mock.patch.object(prices.solve_cache, "cached_json", side_effect=lambda key, compute: compute()):
        result = prices.solved_prices_at_wages([], {"labourer": 1.0}, entries, civilization_id="rome_100ad", interest_rate=rate)
    prices.reset_caches_for_tests()
    return result, solve_json.calls


at_start, calls_at_start = price_at(STARTING_RATE)
check("a solve at the starting rate is cold: one solve, from no prices", len(calls_at_start) == 1 and calls_at_start[0]["initial"] is None,
      calls_at_start)
away, calls_away = price_at(STARTING_RATE + 0.04)
check("a solve at another rate first solves at the starting rate, cold",
      calls_away[0]["rate"] == STARTING_RATE and calls_away[0]["initial"] is None, calls_away)
check("...and starts the solve at its own rate from that solve's prices",
      calls_away[1]["rate"] == STARTING_RATE + 0.04 and calls_away[1]["initial"] == at_start.prices_in_labour_hours, calls_away)
check("the in-game solve stops at the engine's tolerance rather than exactly", all(call["in_game"] for call in calls_away))
farther, _calls = price_at(STARTING_RATE + 0.09)
again, _calls = price_at(STARTING_RATE + 0.04)
check("a solve's answer does not depend on which solves ran before it", again.prices_in_labour_hours == away.prices_in_labour_hours)
elsewhere, calls_elsewhere = price_at(STARTING_RATE + 0.04, entries={"another": {"requires_node": None}})
check("a catalogue other than the game's is solved exactly, with no warm start",
      len(calls_elsewhere) == 1 and calls_elsewhere[0]["initial"] is None and not calls_elsewhere[0]["in_game"], calls_elsewhere)
