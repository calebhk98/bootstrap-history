"""Twin-run divergence probe: two spin-ups of one opening that differ only by households' cash times (1 + eps),
stepped side by side. Each year the two exported records are flattened to numeric leaves and compared.

Writes one JSON line per year: stage, year, the settle quantities of both, and per top-level record section the count
of leaves, the share that differ, the median and the largest relative difference; and the leaves that differ most.

Usage: python3 twin_probe.py <civ> <eps> <out.jsonl> [first_years] [trimmed_years]
"""
import json
import math
import random
import sys
import time

from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites
from sim.markets.spin_up import spin_up_years
from sim.markets.spin_up_ensemble import perturb_household_cash
from sim.markets.spin_up_year import watched_goods

civ, eps, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
first_years, trimmed_years = spin_up_years()
if len(sys.argv) > 4:
    first_years = int(sys.argv[4])
if len(sys.argv) > 5:
    trimmed_years = int(sys.argv[5])


def flatten(value, path, into):
    """Numeric leaves of a plain record, by path."""
    if isinstance(value, dict):
        for key in value:
            flatten(value[key], path + "/" + str(key), into)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            flatten(item, path + "/" + str(index), into)
    elif isinstance(value, bool):
        into[path] = float(value)
    elif isinstance(value, (int, float)):
        into[path] = float(value)
    elif hasattr(value, "item") and not isinstance(value, str):
        try:
            into[path] = float(value.item())
        except (TypeError, ValueError):
            pass
    elif hasattr(value, "tolist"):
        flatten(value.tolist(), path, into)


def relative(first, second):
    scale = max(abs(first), abs(second))
    if scale == 0.0 or not math.isfinite(scale):
        return 0.0
    return abs(first - second) / scale


DETAIL_YEARS = int(__import__("os").environ.get("TWIN_DETAIL_YEARS", "3"))
DETAIL_THRESHOLD = 1e-6


def compare(record_a, record_b, detail=None):
    sections = {}
    worst = []
    for section in record_a:
        leaves_a, leaves_b = {}, {}
        flatten(record_a[section], section, leaves_a)
        flatten(record_b.get(section), section, leaves_b)
        shared = leaves_a.keys() & leaves_b.keys()
        differences = sorted(((relative(leaves_a[path], leaves_b[path]), path) for path in shared), reverse=True)
        values = [difference for difference, _path in differences]
        differing = [value for value in values if value > 0.0]
        sections[section] = {
            "leaves": len(shared), "only_one_side": len(leaves_a.keys() ^ leaves_b.keys()),
            "differing_share": len(differing) / len(values) if values else 0.0,
            "median_of_differing": sorted(differing)[len(differing) // 2] if differing else 0.0,
            "p90": values[len(values) // 10] if values else 0.0,
            "largest": values[0] if values else 0.0}
        worst.extend((difference, path, leaves_a[path], leaves_b[path]) for difference, path in differences[:6])
        if detail is not None:
            detail.extend((difference, path, leaves_a[path], leaves_b[path]) for difference, path in differences
                          if difference > DETAIL_THRESHOLD)
            detail.extend((9.0, path, leaves_a.get(path), leaves_b.get(path)) for path in sorted(leaves_a.keys() ^ leaves_b.keys()))
    worst.sort(reverse=True)
    return sections, worst[:25]


started = time.time()
_tree, _prices, nodes, _wages, _goods = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
twins = []
for factor in (1.0, 1.0 + eps):
    economy = economy_api.blank_economy(setup)
    economy_api.begin_spin_up(economy)
    if factor != 1.0:
        perturb_household_cash(economy, factor)
    twins.append(economy)
watched = watched_goods(twins[0])
inputs = [EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
          for economy in twins]
print("opened", round(time.time() - started, 1), "seconds", flush=True)

years_done = 0
with open(out, "w") as handle:
    handle.write(json.dumps({"civ": civ, "eps": eps, "watched": watched}) + "\n")
    for stage, years in (("first", first_years), ("trimmed", trimmed_years)):
        if stage == "trimmed":
            for economy in twins:
                economy_api.trim_workforce_to_expected_hours(economy)
        for year in range(years):
            tick = time.time()
            outcomes = [economy.step(year_inputs) for economy, year_inputs in zip(twins, inputs)]
            states = []
            for economy, outcome in zip(twins, outcomes):
                state = dict(economy_api.spin_up_state(economy, outcome))
                state.update({"price_level": outcome.basket_price_level, "rate": economy_api.interest_rate(economy),
                              "money_supply": outcome.money_supply, "wage": outcome.wages.get(setup.unskilled_trade),
                              "prices": {good: outcome.prices.get(good) for good in watched}})
                states.append(state)
            flows = []
            for outcome in outcomes:
                leaves = {}
                flatten({"prices": outcome.prices, "wages": outcome.wages, "output": outcome.output,
                         "hunger": outcome.hunger_by_tile}, "outcome", leaves)
                flows.append(leaves)
            shared = flows[0].keys() & flows[1].keys()
            flow_differences = sorted(((relative(flows[0][path], flows[1][path]), path, flows[0][path], flows[1][path])
                                       for path in shared), reverse=True)
            detail = [] if years_done < DETAIL_YEARS else None
            sections, worst = compare(economy_api.export_record(twins[0], ()), economy_api.export_record(twins[1], ()), detail)
            if detail is not None:
                with open(out + ".detail%d.json" % years_done, "w") as detail_handle:
                    json.dump(detail, detail_handle)
            years_done += 1
            row = {"stage": stage, "year": year, "seconds": round(time.time() - tick, 1), "states": states,
                   "sections": sections, "worst": worst,
                   "outcome": {"leaves": len(shared), "only_one_side": len(flows[0].keys() ^ flows[1].keys()),
                               "differing_share": sum(1 for item in flow_differences if item[0] > 0.0) / max(1, len(shared)),
                               "median": flow_differences[len(flow_differences) // 2][0] if flow_differences else 0.0,
                               "p90": flow_differences[len(flow_differences) // 10][0] if flow_differences else 0.0,
                               "largest": flow_differences[0][0] if flow_differences else 0.0,
                               "worst": flow_differences[:15]}}
            handle.write(json.dumps(row, default=float) + "\n")
            handle.flush()
            print(stage, year, row["seconds"], "s; outcome median", "%.3g" % row["outcome"]["median"], "p90", "%.3g" % row["outcome"]["p90"],
                  "largest", "%.3g" % row["outcome"]["largest"], flush=True)
