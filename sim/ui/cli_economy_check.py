"""`economy-check`: play a short game per civilisation and seed, then print the agent economy's health."""
import math
import random

from sim.engine.ui_port import Sim, civilization_ids, default_civilisation_id, load, load_civ

FIGURE_LABELS = (
    ("staple_volatility", "std dev of the staple's yearly log price change"),
    ("metal_volatility", "median of the same over the metals"),
    ("hired_share", "median share of offered hours hired"),
    ("hunger_share", "mean food floor short over the floor needed"),
    ("staple_over_labour", "median staple price over its labour cost"),
)


def _split(text):
    return [part.strip() for part in (text or "").split(",") if part.strip()]


def _format(value):
    return "n/a" if value is None or math.isnan(value) else "%.4g" % value


def check_one(nodes, civ_id, seed, years, metals, staple=None):
    """Play `years` years of `civ_id` and return the port's health report (None off the agent economy)."""
    game = Sim(nodes, [], random.Random(seed), events=False, manual=True, civ=load_civ(civ_id),
               cfg={"agent_economy": True})
    game.done_year = {}
    for _year in range(years):
        game.step()
    return game.economy.health(metals, staple)


def cmd_economy_check(args):
    _tree, _prices, nodes, _wages, _goods = load()
    civs = _split(args.civs) or [default_civilisation_id()]
    if civs == ["all"]:
        civs = civilization_ids()
    seeds = [int(seed) for seed in _split(args.seeds)] or [1]
    metals = tuple(_split(args.metals))
    for civ_id in civs:
        for seed in seeds:
            report = check_one(nodes, civ_id, seed, args.years, metals, args.staple or None)
            print("%s, seed %d, %d years" % (civ_id, seed, args.years))
            if report is None or not report["figures"]:
                print("  no agent economy figures (the civilisation holds no tiles or the economy is off)")
                continue
            print("  staple %s, metals %s" % (report["staple"], ", ".join(report["metals"]) or "none"))
            for key, meaning in FIGURE_LABELS:
                print("  %-20s %8s  %s" % (key, _format(report["figures"].get(key)), meaning))
    return 0
