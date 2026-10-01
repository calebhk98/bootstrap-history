#!/usr/bin/env python3
"""Measure foreign trade: yearly imports and exports by commodity over a run,
the route's legs, and a shortage-year price ratio with and without trade.

    python3 sim/foreign_trade_report.py --years 100
    python3 sim/foreign_trade_report.py --years 100 --partner <civilisation id> [--civilization <civilisation id>]

Partners are switched on for the run whether or not the data file enables
them, so the report is how an economy is judged before enabling it.
"""
import argparse
import collections
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
while HERE in sys.path:
    sys.path.remove(HERE)

from sim import simulator as simulator_module  # noqa: E402

TREE, PRICES, NODES, WAGES, GOODS = simulator_module.load()
GOAL = TREE["meta"]["goal_node"]
_LABOUR, ORDER, _BUDGET = simulator_module.load_strategy("recommended", NODES, GOAL)
SHORTAGE_COMMODITIES = ("cloth", "iron", "copper")
SHORTAGE_CAPACITY_SHARE = 0.3


def build(civilization_id, partner_id):
    game = simulator_module.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
                                civ=simulator_module.load_civ(civilization_id),
                                cfg={"start_capital": 1e9})
    game.goal, game.done_year = GOAL, {}
    game.foreign_economies = (lambda: [partner_id]) if partner_id else (lambda: [])
    return game


def print_flows(game, years):
    imports, exports = collections.defaultdict(float), collections.defaultdict(float)
    for _year in range(years):
        game.step()
        for commodity, entry in game.state.economy.market_book.items():
            flow = entry.get("trade_tonnes", 0.0)
            if flow > 0.0:
                imports[commodity] += flow
            elif flow < 0.0:
                exports[commodity] -= flow
    for title, flows in (("imports", imports), ("exports", exports)):
        print("%s, tonnes a year averaged over %d years:" % (title, years))
        for commodity, total in sorted(flows.items(), key=lambda pair: -pair[1]):
            print("  %-22s %12.1f" % (commodity, total / years))


def print_shortage(civilization_id, partner_id):
    print("price over long-run cost when capacity is cut to %.0f%%:" % (
        100.0 * SHORTAGE_CAPACITY_SHARE))
    for commodity in SHORTAGE_COMMODITIES:
        ratios = []
        for partner in (None, partner_id):
            game = build(civilization_id, partner)
            game._market_entry(commodity)["capacity_tonnes"] *= SHORTAGE_CAPACITY_SHARE
            ratios.append(game.market_price_ratio(commodity))
        print("  %-12s no trade %.2f   with trade %.2f" % (commodity, ratios[0], ratios[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--civilization", default=None, help="default: the game's default civilisation")
    parser.add_argument("--partner", required=True, help="a civilisation id from data/civilizations")
    parser.add_argument("--years", type=int, default=100)
    arguments = parser.parse_args()
    if arguments.civilization is None:
        from sim.engine.default_civilisation import default_civilisation_id
        arguments.civilization = default_civilisation_id()
    game = build(arguments.civilization, arguments.partner)
    print("route to %s:" % arguments.partner)
    for origin, destination, mode, distance_km, cost in game.foreign_route_legs(arguments.partner):
        print("  %s -%s-> %s  %.0f km  %.1f per tonne" % (origin, mode, destination, distance_km, cost))
    print_flows(game, arguments.years)
    print_shortage(arguments.civilization, arguments.partner)
    return 0


if __name__ == "__main__":
    sys.exit(main())
