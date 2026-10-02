#!/usr/bin/env python3
"""Measure foreign trade: yearly imports and exports by commodity over a run,
the route's legs, and a shortage-year price ratio with and without trade.

    python3 sim/foreign_trade_report.py --years 100
    python3 sim/foreign_trade_report.py --years 100 --partner <civilisation id> [--civilization <civilisation id>]
    python3 sim/foreign_trade_report.py --years 100 --partner <civilisation id> --baseline

Besides the totals it prints, by decade: tonnes in and out, the balance of payments (goods in and
out, coin paid out, the home coin stock and price level) and the price over long-run cost of the
most traded goods. `--baseline` runs the same years with no partner for comparison.

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


DECADE_YEARS = 10
MAIN_GOODS = 3


def _snapshot(game, partner_id):
    """The year just closed: tonnes by commodity (positive imported) and the ledger's totals."""
    flows = {commodity: entry.get("trade_tonnes", 0.0)
             for commodity, entry in game.state.economy.market_book.items()
             if entry.get("trade_tonnes", 0.0)}
    ratios = {commodity: entry.get("price_ratio", 1.0)
              for commodity, entry in game.state.economy.market_book.items()}
    bop = game.foreign_balance_of_payments(partner_id) if partner_id else {}
    return flows, ratios, bop


def print_decades(history, partner_id):
    """One row per decade: mean tonnes in and out a year, goods and coin moved in the decade, the
    home coin stock and price level at its end, and the most traded goods' price ratios."""
    totals = collections.defaultdict(float)
    for flows, _ratios, _bop in history:
        for commodity, tonnes in flows.items():
            totals[commodity] += abs(tonnes)
    main = [commodity for commodity, _total in sorted(totals.items(), key=lambda pair: -pair[1])][:MAIN_GOODS]
    print("by decade (tonnes a year; money in home units; price ratio is spot over long-run cost):")
    print("  %-6s %9s %9s %14s %14s %14s %7s %9s %s" % (
        "years", "in t", "out t", "goods in", "goods out", "coin stock", "level", "lift t",
        " ".join("%12s" % commodity[:12] for commodity in main)))
    previous = {"goods_in_value": 0.0, "goods_out_value": 0.0}
    for start in range(0, len(history), DECADE_YEARS):
        block = history[start:start + DECADE_YEARS]
        into = sum(sum(max(0.0, tonnes) for tonnes in flows.values()) for flows, _r, _b in block)
        out = sum(sum(max(0.0, -tonnes) for tonnes in flows.values()) for flows, _r, _b in block)
        bop = block[-1][2] or {}
        goods_in = bop.get("goods_in_value", 0.0) - previous["goods_in_value"]
        goods_out = bop.get("goods_out_value", 0.0) - previous["goods_out_value"]
        previous = {"goods_in_value": bop.get("goods_in_value", 0.0),
                    "goods_out_value": bop.get("goods_out_value", 0.0)}
        print("  %-6s %9.1f %9.1f %14.4g %14.4g %14.4g %7.3f %9.1f %s" % (
            "%d-%d" % (start + 1, start + len(block)), into / len(block), out / len(block),
            goods_in, goods_out, bop.get("home_coin_stock_units", 0.0), bop.get("home_price_level", 1.0),
            bop.get("fleet_lift_tonnes_per_year", 0.0),
            " ".join("%12.3f" % block[-1][1].get(commodity, 1.0) for commodity in main)))
    if partner_id:
        print("partner price level at the end: %.3f" % history[-1][2].get("partner_price_level", 1.0))


def print_flows(game, years, partner_id=None):
    imports, exports = collections.defaultdict(float), collections.defaultdict(float)
    history = []
    for _year in range(years):
        game.step()
        history.append(_snapshot(game, partner_id))
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
    print_decades(history, partner_id)


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
    parser.add_argument("--baseline", action="store_true",
                        help="run the same years with no partner, for comparison")
    arguments = parser.parse_args()
    if arguments.civilization is None:
        from sim.engine.default_civilisation import default_civilisation_id
        arguments.civilization = default_civilisation_id()
    game = build(arguments.civilization, None if arguments.baseline else arguments.partner)
    if not arguments.baseline:
        print("route to %s:" % arguments.partner)
        for origin, destination, mode, distance_km, cost in game.foreign_route_legs(arguments.partner):
            print("  %s -%s-> %s  %.0f km  %.1f per tonne" % (origin, mode, destination, distance_km, cost))
    print_flows(game, arguments.years, None if arguments.baseline else arguments.partner)
    if not arguments.baseline:
        print_shortage(arguments.civilization, arguments.partner)
    return 0


if __name__ == "__main__":
    sys.exit(main())
