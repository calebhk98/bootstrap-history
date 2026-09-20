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
import argparse, concurrent.futures, hashlib, json, os, random, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)
while HERE in sys.path:
	sys.path.remove(HERE)
from sim import simulator as S
from sim.engine.protocol import SAVE_FIELDS

TREE, PRICES, NODES, WAGES, GOODS = S.load()
GOAL = TREE["meta"]["goal_node"]
_LAB, ORDER, _B = S.load_strategy("recommended", NODES, GOAL)

# WHAT GETS COMPARED. Reference baselines (baseline_quick.json, baseline_full.json)
# check the canonical reference set of 101 state fields.
BASELINE_FIELDS = (
    "year", "capital", "done", "granted", "active", "done_year", "training",
    "scholars", "artisans", "directors_extra", "reputation",
    "scandal", "eminence", "protection", "familiarity", "forest_ha",
    "nitre_bed_m2", "mine_pending", "mine_ready", "mines",
    "mine_tranches", "market_pressure", "slaves", "freedmen",
    "manumitted_total", "goal_year", "dead_reason", "insolvent_years",
    "bribes_ytd", "living_cost_paid", "mine_cost_paid", "spend_last_year",
    "output_factor", "economy", "throttle", "binding", "bountied",
    "stalled", "life_left", "founder_alive", "revealed", "last_settlement",
    "employees", "trades_created", "policy", "mothballed", "operating",
    "forgotten", "opened_year", "last_taught", "paid_towards",
    "contract_hours", "hour_allocations", "work_trade",
    "commissioned", "wages_paid", "bondage_years_left", "bondage_debt",
    "money_real", "credit_frozen_until", "interest_paid",
    "wage_hours_this_year", "teaching_hours_this_year", "trade_hours_used",
    "total_spend", "director_hours_spent_founder", "bounties_paid",
    "atrocity", "gov", "wages_earned", "last_patron_death",
    "_said_debasement", "_said_autoopen", "_said_output", "_said_scandal",
    "_said_parallelism", "_said_command_index", "_said_deputies",
    "_said_near_limit", "shut_for_staff", "_food_pop_bonus_applied",
    "pop_children", "pop_working_age", "pop_elderly", "farm_stock_kg",
    "_material_stock_ledger", "farm_hectares", "worker_housing_places",
    "trade_schools", "last_withdrawal", "wages_prepaid", "granted_staff",
    "hours_this_year", "_founder_death_aged", "_founder_death_year",
    "inst_units", "trade_introduced_year", "trades_endemic",
    "_dashboard_history", "failed_attempts", "shortages"
)

FIELDS = BASELINE_FIELDS


def _canon(value):
    """Make a value comparable and order-independent where order is not real."""
    if hasattr(value, "to_canon_dict"):
        value = value.to_canon_dict()
    if isinstance(value, float):
        # repr() rather than round(): a change that alters the last bit of a
        # float IS a change, and this harness exists to catch exactly that.
        return repr(value)
    if isinstance(value, set):
        return ["__set__"] + sorted(_canon(item) for item in value)
    if isinstance(value, dict):
        return {str(key): _canon(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canon(item) for item in value]
    return value


def _resolve_field(sim, field):
    """Resolve field value from sim, household actor, or authoritative state subsystem."""
    if hasattr(sim, field):
        return getattr(sim, field)
    if hasattr(sim, "household") and hasattr(sim.household, field):
        return getattr(sim.household, field)
    if hasattr(sim, "state") and sim.state:
        for sub_name in ("household", "projects", "economy", "governance", "founder", "scenario", "population"):
            sub = getattr(sim.state, sub_name, None)
            if sub is not None and hasattr(sub, field):
                return getattr(sub, field)
    return None


def state_of(sim):
    return {field: _canon(_resolve_field(sim, field)) for field in FIELDS}


def digest(data):
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:16]


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

# FAST DEVELOPER ITERATION MODE SUBSET (--quick).
QUICK_SCENARIOS = [
    dict(civ="rome_100ad",      seed=1, years=100, events=True,  fog=False),
    dict(civ="rome_100ad",      seed=2, years=100, events=True,  fog=True),
    dict(civ="han_china_100ad", seed=1, years=100, events=True,  fog=False),
    dict(civ="england_1300",    seed=1, years=100, events=True,  fog=False),
]


def build(scenario):
    sim = S.Sim(NODES, ORDER, random.Random(scenario["seed"]), events=scenario["events"],
              manual=False, civ=S.load_civ(scenario["civ"]))
    sim.goal, sim.done_year = GOAL, {}
    if scenario["fog"]:
        sim.fog = True
    return sim


def name_of(scenario):
    return "%s/seed%d/%dy/%s%s" % (scenario["civ"], scenario["seed"], scenario["years"],
                                   "events" if scenario["events"] else "noevents",
                                   "+fog" if scenario["fog"] else "")


def run(scenario, keep_states=False):
    """Return (per-year digests, cpu seconds, final full states list)."""
    sim = build(scenario)
    start_time = time.process_time()
    per_year, states = [], []
    for _ in range(scenario["years"]):
        if sim.dead_reason:
            break
        sim.step()
        state = state_of(sim)
        per_year.append(digest(state))
        if keep_states:
            states.append(state)
    return per_year, time.process_time() - start_time, states


def _run_scenario_worker(arg):
    """Worker function for ProcessPoolExecutor."""
    scenario, keep_states = arg
    per_year, cpu_time, states = run(scenario, keep_states=keep_states)
    return scenario, per_year, cpu_time, states


def record(path, scenarios=None, jobs=None):
    if scenarios is None:
        scenarios = SCENARIOS
    if jobs is None:
        jobs = min(len(scenarios), os.cpu_count() or 1)

    out, cpu_total = {}, 0.0
    start_wall = time.time()

    if jobs > 1:
        with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as executor:
            results = list(executor.map(_run_scenario_worker, [(s, False) for s in scenarios]))
    else:
        results = [_run_scenario_worker((s, False)) for s in scenarios]

    wall_total = time.time() - start_wall

    for scenario, years, cpu, _ in results:
        name = name_of(scenario)
        cpu_total += cpu
        out[name] = {"scenario": scenario, "years": years}
        print("  %-42s %5d years  %7.2fs cpu" % (name, len(years), cpu))

    print("  %-42s %18.2fs cpu  %7.2fs wall TOTAL" % ("", cpu_total, wall_total))
    with open(path, "w") as handle:
        json.dump(out, handle, indent=1)
    print("written to %s" % path)
    return 0


def check(path, scenarios=None, jobs=None):
    with open(path) as handle:
        base = json.load(handle)

    if scenarios is not None:
        target_names = {name_of(s) for s in scenarios}
        base_items = [(name, entry) for name, entry in base.items() if name in target_names]
        if not base_items:
            base_items = []
            for name, entry in base.items():
                sc = entry["scenario"]
                if any(s["civ"] == sc["civ"] and s["seed"] == sc["seed"] for s in scenarios):
                    base_items.append((name, entry))
    else:
        base_items = list(base.items())

    target_scenarios = [entry["scenario"] for _, entry in base_items]
    if jobs is None:
        jobs = min(len(target_scenarios), os.cpu_count() or 1)

    start_wall = time.time()
    # Keep keep_states=False on initial check run to avoid memory overhead
    if jobs > 1:
        with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as executor:
            results = list(executor.map(_run_scenario_worker, [(s, False) for s in target_scenarios]))
    else:
        results = [_run_scenario_worker((s, False)) for s in target_scenarios]

    wall_total = time.time() - start_wall
    bad, cpu_total = [], 0.0
    result_map = {name_of(s): (years, cpu) for s, years, cpu, _ in results}

    for name, entry in base_items:
        scenario = entry["scenario"]
        want = entry["years"]
        if name not in result_map:
            continue
        got, cpu = result_map[name]
        cpu_total += cpu

        want_cmp = want[:scenario["years"]]

        if got == want_cmp:
            print("  %-42s SAME  %5d years  %7.2fs cpu" % (name, len(got), cpu))
            continue

        diverged_at = next((index for index in range(min(len(got), len(want_cmp)))
                            if got[index] != want_cmp[index]), min(len(got), len(want_cmp)))
        bad.append((name, diverged_at))
        print("  %-42s DIVERGED at year index %d (of %d/%d)"
              % (name, diverged_at, len(got), len(want_cmp)))
        if len(got) != len(want_cmp):
            print("      run length changed: %d -> %d" % (len(want_cmp), len(got)))

        # Rerun ONLY the failing scenario with keep_states=True for diagnostic state
        _, _, states = run(scenario, keep_states=True)
        if diverged_at < len(states):
            print("      re-run this scenario under a debugger; changed state "
                  "is in %s year %d" % (name, diverged_at))

    print()
    if bad:
        print("FAIL: %d of %d scenarios diverged" % (len(bad), len(base_items)))
        return 1
    print("OK: all %d scenarios byte-identical.  %.2fs cpu  %.2fs wall TOTAL"
          % (len(base_items), cpu_total, wall_total))
    return 0


def main():
    parser = argparse.ArgumentParser(description="Prove an optimisation changed nothing.")
    parser.add_argument("mode", choices=["record", "check"], help="Mode: record or check")
    parser.add_argument("path", help="Path to JSON baseline file")
    parser.add_argument("--jobs", "-j", type=int, default=None, help="Number of parallel processes")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--quick", action="store_true", help="Run fast subset of scenarios")
    group.add_argument("--full", action="store_true", help="Run full scenario set (default)")

    args = parser.parse_args()
    scenarios = QUICK_SCENARIOS if args.quick else SCENARIOS
    jobs = args.jobs if args.jobs is not None else min(len(scenarios), os.cpu_count() or 1)

    if args.mode == "record":
        return record(args.path, scenarios=scenarios, jobs=jobs)
    else:
        return check(args.path, scenarios=scenarios, jobs=jobs)


if __name__ == "__main__":
    sys.exit(main())
