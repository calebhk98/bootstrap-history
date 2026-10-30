#!/usr/bin/env python3
"""Prove a refactor kept the game the same, year by year, and say where it did not.

    python3 -m sim.tests.equiv record PATH --tier micro|full|long|stress
    python3 -m sim.tests.equiv check PATH --tier micro|full|long|stress [--base-checkout DIR]
    python3 -m sim.tests.equiv record PATH --tier micro --hash-seeds 0,1     # same bytes under both hash seeds?

Each year after `sim.step()` the whole saved state (`saveload.state_text`) is parsed and flattened to
path -> canonical value leaves; free prose of log records is dropped, keeping kind and facts. The leaves are hashed
per top-level section, and the random generator state is hashed on its own, so a draw made in a different order
shows as the generator differing while no section does.

State may move between dataclasses during a refactor. `equiv_fields.py` holds RELOCATIONS (ordered old -> new path
prefix rewrites, applied to this checkout's leaves first) and IGNORED (prefixes dropped after that, for bookkeeping
only the new build has). A relocated field is still compared; an ignored one is not.

`check` reports the first diverging year, the sections and whether the generator differs. With `--base-checkout`
(a worktree of the base commit) it re-runs the scenario to that year in both checkouts and prints the first
differing leaves with both values.

The game is built with the quick tier's short spin-up (recorded in the file and reused by `check`).
"""
import argparse, concurrent.futures, json, os, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from sim.tests import equiv_core

VALUE_WIDTH = 100


def scenario_name(scenario):
    """Fingerprint's name, plus the stress tier's marks so its scenarios do not share one."""
    from sim.tests import fingerprint
    name = fingerprint.name_of(scenario)
    if scenario.get("stress"):
        name += "+stress"
    if scenario.get("seats", 1) > 1:
        name += "+%dseats" % scenario["seats"]
    return name


def tier_scenarios(tier):
    """The scenarios of a tier; the scenario definitions are fingerprint's."""
    from sim.tests import fingerprint
    quick = fingerprint.QUICK_SCENARIOS
    if tier == "long":
        return [dict(scenario) for scenario in quick]
    if tier == "full":
        return [dict(scenario, years=40) for scenario in quick]
    if tier == "micro":
        return [dict(quick[0], years=15), dict(quick[1], civ="han_china_100ad", seed=2, years=15)]
    if tier == "stress":   # sim/tests/equiv_stress.py: every hazard kind and the rare events, one seat and two
        return [dict(quick[0], years=12, stress=True), dict(quick[0], years=12, stress=True, seats=2)]
    raise SystemExit("unknown tier %r" % tier)


def first_divergence(recorded_years, got_years):
    """None when equal, else (index, sections that differ, whether the generator differs, note).
    A year is [rng hash, {section: hash}]; a length change diverges where the shorter run ended."""
    for index in range(min(len(recorded_years), len(got_years))):
        if recorded_years[index] != got_years[index]:
            sections = equiv_core.differing_sections(recorded_years[index][1], got_years[index][1])
            return index, sections, recorded_years[index][0] != got_years[index][0], ""
    if len(recorded_years) != len(got_years):
        return min(len(recorded_years), len(got_years)), [], False, \
            "run length changed: %d -> %d years" % (len(recorded_years), len(got_years))
    return None


def _year_entry(leaves, rng):
    return [rng, equiv_core.section_hashes(leaves)]


def _prepare(spin_up):
    from sim.tests import equiv_run
    return equiv_run.prepare_environment(spin_up)


def _record_worker(arguments):
    scenario, spin_up = arguments
    from sim.tests import equiv_run
    _prepare(spin_up)
    years, started = [], time.time()
    equiv_run.run_years(scenario, lambda index, leaves, rng: years.append(_year_entry(leaves, rng)))
    return years, time.time() - started


def _check_worker(arguments):
    scenario, spin_up, recorded_years = arguments
    from sim.tests import equiv_run
    _prepare(spin_up)
    got, started = [], time.time()
    state = {"divergence": None}

    def on_year(index, leaves, rng):
        got.append(_year_entry(leaves, rng))
        if recorded_years[index:index + 1] != [got[-1]]:
            state["divergence"] = first_divergence(recorded_years[:index + 1], got)
            return False
        return None

    equiv_run.run_years(scenario, on_year)
    divergence = state["divergence"] or first_divergence(recorded_years, got)
    return divergence, len(got), time.time() - started


def _map(worker, work, jobs):
    if jobs > 1 and len(work) > 1:
        with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as executor:
            return list(executor.map(worker, work))
    return [worker(item) for item in work]


def default_jobs(count):
    try:
        cores = len(os.sched_getaffinity(0))
    except AttributeError:
        cores = os.cpu_count() or 1
    return max(1, min(count, cores))


def record(path, tier, jobs, spin_up=None):
    from sim.tests import fingerprint
    spin_up = _prepare(spin_up)
    scenarios = tier_scenarios(tier)
    started = time.time()
    results = _map(_record_worker, [(scenario, spin_up) for scenario in scenarios], jobs or default_jobs(len(scenarios)))
    output = {"meta": {"tier": tier, "spin_up": spin_up}, "scenarios": {}}
    for scenario, (years, seconds) in zip(scenarios, results):
        name = scenario_name(scenario)
        output["scenarios"][name] = {"scenario": scenario, "years": years}
        print("  %-42s %4d years  %7.1fs" % (name, len(years), seconds))
    with open(path, "w") as handle:
        json.dump(output, handle, separators=(",", ":"))
    print("recorded %s (%s tier) in %.1fs wall" % (path, tier, time.time() - started))
    return 0


def _clip(text):
    return text if len(text) <= VALUE_WIDTH else text[:VALUE_WIDTH] + "..."


def explain_with_base(scenario, year_index, sections, base_checkout, spin_up, limit=20):
    """Print the first differing leaves between the base checkout and this one at the diverging year."""
    from sim.tests import equiv_run
    with tempfile.TemporaryDirectory() as scratch:
        base_path = os.path.join(scratch, "base.json.gz")
        process = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "equiv_dump.py"), base_checkout, HERE, json.dumps(scenario),
             str(year_index), base_path, "raw", spin_up], cwd=base_checkout)
        current_leaves, _ = equiv_run.leaves_at_year(scenario, year_index)
        if process.wait() != 0:
            print("      base run failed in %s" % base_checkout)
            return
        base_leaves, _ = equiv_run.read_dump(base_path)
    shown, total = equiv_core.diff_leaves(base_leaves, current_leaves, limit, sections or None)
    print("      %d differing leaves; first %d:" % (total, len(shown)))
    if not total:
        print("      every value is equal: only the random draws differ (a draw made in another order or count)")
    for leaf_path, base_value, current_value in shown:
        print("        %s\n            base    %s\n            current %s"
              % (leaf_path, _clip(base_value), _clip(current_value)))


def check(path, tier, jobs, base_checkout=None):
    with open(path) as handle:
        recorded = json.load(handle)
    if recorded["meta"]["tier"] != tier:
        raise SystemExit("%s holds the %s tier, not %s" % (path, recorded["meta"]["tier"], tier))
    spin_up = _prepare(recorded["meta"]["spin_up"])
    names = sorted(recorded["scenarios"])
    work = [(recorded["scenarios"][name]["scenario"], spin_up, recorded["scenarios"][name]["years"]) for name in names]
    started = time.time()
    results = _map(_check_worker, work, jobs or default_jobs(len(work)))
    failed = 0
    for name, (scenario, _spin, _years), (divergence, ran, seconds) in zip(names, work, results):
        if divergence is None:
            print("  %-42s SAME  %4d years  %7.1fs" % (name, ran, seconds))
            continue
        failed += 1
        index, sections, rng_differs, note = divergence
        print("  %-42s DIVERGED at year %d (0-based)  sections: %s  random state %s%s"
              % (name, index, ", ".join(sections) or "none", "DIFFERS" if rng_differs else "same",
                 "  " + note if note else ""))
        if base_checkout and not note:
            explain_with_base(scenario, index, sections, base_checkout, spin_up)
        elif not base_checkout:
            print("      pass --base-checkout DIR for the differing leaves")
    print("%s: %d of %d scenarios diverged, %.1fs wall" % ("FAIL" if failed else "OK", failed, len(names),
                                                            time.time() - started))
    return 1 if failed else 0


def check_hash_seeds(path, tier, seeds, jobs):
    """Record the tier once per PYTHONHASHSEED (concurrently) and compare the files byte for byte."""
    per_run_jobs = max(1, (jobs or default_jobs(4)) // len(seeds))
    paths, processes = [], []
    for seed in seeds:
        seed_path = "%s.hashseed%s" % (path, seed)
        paths.append(seed_path)
        environment = dict(os.environ, PYTHONHASHSEED=str(seed))
        processes.append(subprocess.Popen(
            [sys.executable, "-m", "sim.tests.equiv", "record", seed_path, "--tier", tier, "--jobs", str(per_run_jobs)],
            cwd=REPO_ROOT, env=environment))
    if any(process.wait() != 0 for process in processes):
        return 1
    contents = [open(seed_path).read() for seed_path in paths]
    if all(content == contents[0] for content in contents):
        os.replace(paths[0], path)
        for extra in paths[1:]:
            os.remove(extra)
        print("DETERMINISTIC: identical under PYTHONHASHSEED %s; written to %s" % (",".join(seeds), path))
        return 0
    loaded = [json.loads(content) for content in contents]
    for name, entry in loaded[0]["scenarios"].items():
        divergence = first_divergence(entry["years"], loaded[1]["scenarios"][name]["years"])
        if divergence:
            print("NOT DETERMINISTIC: %s year %d sections %s random state %s"
                  % (name, divergence[0], divergence[1], "differs" if divergence[2] else "same"))
    print("files kept: %s" % ", ".join(paths))
    return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="Year-by-year whole-state equivalence of two builds.")
    parser.add_argument("mode", choices=["record", "check"])
    parser.add_argument("path")
    parser.add_argument("--tier", required=True, choices=["micro", "full", "long", "stress"])
    parser.add_argument("--jobs", "-j", type=int, default=None, help="parallel scenarios (default min(scenarios, cores))")
    parser.add_argument("--base-checkout", default=None, help="worktree of the base commit, for leaf-level diffs")
    parser.add_argument("--hash-seeds", default=None, help="record: comma list of PYTHONHASHSEED values to compare")
    parser.add_argument("--spin-up", default=None, help="override ROME_SPIN_UP_YEARS for a record")
    args = parser.parse_args(argv)
    if args.mode == "record" and args.hash_seeds:
        return check_hash_seeds(args.path, args.tier, args.hash_seeds.split(","), args.jobs)
    if args.mode == "record":
        return record(args.path, args.tier, args.jobs, args.spin_up)
    return check(args.path, args.tier, args.jobs, args.base_checkout and os.path.abspath(args.base_checkout))


if __name__ == "__main__":
    sys.exit(main())
