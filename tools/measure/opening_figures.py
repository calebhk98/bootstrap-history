"""A civilisation's opening, dumped for comparing two builds, and the comparison. Run from a checkout's root:

    python3 tools/measure/opening_figures.py dump CIV EMPTY_CACHE_DIR OUT.json
    python3 tools/measure/opening_figures.py compare FIRST.json SECOND.json

`dump` opens a new game of CIV on an empty cache directory (so the opening is solved, not read), stops before the
hidden spin-up, and writes the solve's seconds and its figures: each producer's capacity, expected sales and yield, each
cohort's income, share wealth and hired household work, every agent's cash, every remembered price and property income.
`compare` prints, per section, how many entries are compared or missing and the median, 95th percentile and worst relative
difference. A Rome opening takes about a minute; compare Rome as well as England (Rome's household plans reach rules
England does not)."""
import json
import os
import random
import sys
import time

SECTIONS = ("producers", "cohort_income", "cohort_share_wealth", "cohort_hired_work", "cash", "prices", "property_income")


class _Stop(Exception):
    pass


def dump(civ_id, cache_directory, out_path):
    os.environ["ROME_CACHE_DIR"] = cache_directory
    sys.path.insert(0, ".")
    from sim.economy import economy as economy_module
    from sim.markets import spin_up_run
    captured = {}
    opening = economy_module.open_economy

    def timed_open(setup):
        started = time.time()
        result = opening(setup)
        captured.update(seconds=time.time() - started, record=result[0], setup=setup)
        return result

    def stop(setup):
        raise _Stop()

    economy_module.open_economy = timed_open
    spin_up_run.spun_up = stop
    from sim.engine.ui_port import Sim, load, load_civ
    _tree, _prices, nodes, _wages, _goods = load()
    try:
        Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ_id))
    except _Stop:
        pass
    record, money = captured["record"], captured["setup"].currency_id
    agents = sorted(list(record.cohorts) + list(record.producers) + list(record.merchants))
    figures = {
        "seconds": captured["seconds"],
        "producers": {key: [each.capacity_runs, each.expected_sales, each.yield_factor] for key, each in sorted(record.producers.items())},
        "cohort_income": {key: each.last_year_income for key, each in sorted(record.cohorts.items())},
        "cohort_share_wealth": {key: (each.share_wealth or 0.0) for key, each in sorted(record.cohorts.items())},
        "cohort_hired_work": {key: each.hired_work_per_person for key, each in sorted(record.cohorts.items())},
        "cash": {agent: record.book.balance(agent, money) for agent in agents},
        "prices": {key: price for key, price in sorted(record.memory.prices.items())},
        "property_income": dict(sorted(record.capital_markets.property_income.items())),
    }
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(figures, handle)
    print("opening seconds", figures["seconds"], "producers", len(figures["producers"]))


def compare(first_path, second_path):
    with open(first_path, encoding="utf-8") as handle:
        first = json.load(handle)
    with open(second_path, encoding="utf-8") as handle:
        second = json.load(handle)
    print("seconds", first["seconds"], second["seconds"])
    for section in SECTIONS:
        left, right = first[section], second[section]
        keys = set(left) | set(right)
        missing = [key for key in keys if key not in left or key not in right]
        differences, worst = [], (0.0, None)
        for key in sorted(keys - set(missing)):
            pairs = list(zip(left[key], right[key])) if isinstance(left[key], list) else [(left[key], right[key])]
            for index, (one, other) in enumerate(pairs):
                difference = abs(one - other) / max(abs(one), abs(other), 1e-9)
                differences.append(difference)
                if difference > worst[0]:
                    worst = (difference, (key, index, one, other))
        differences.sort()
        median = differences[len(differences) // 2] if differences else 0.0
        high = differences[int(len(differences) * 0.95)] if differences else 0.0
        print("%-20s compared %6d  missing %4d  median %.1e  95th %.1e  worst %.2e %s"
              % (section, len(differences), len(missing), median, high, worst[0], worst[1]))


if __name__ == "__main__":
    if sys.argv[1] == "dump":
        dump(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        compare(sys.argv[2], sys.argv[3])
