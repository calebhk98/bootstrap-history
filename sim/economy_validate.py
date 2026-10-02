#!/usr/bin/env python3
"""Play games on the agent economy and report whether its behaviour falls in plausible ranges.

    python3 sim/economy_validate.py                    every civilisation, three seeds, forty years
    python3 sim/economy_validate.py --years 60 --seeds 1,2,3,4 --civs <civilisation>,<civilisation>

Distributions and directions, never dated events (CLAUDE.md 4.1, 4.2):
  static   share of traded goods whose price stays within 5% of its first-year value every year
  grain/metal  yearly price volatility of wheat against the median of the metals
  wage     an hour of unskilled work in kg of wheat, median over the run
  harvest  correlation between the harvest weather and the change in the wheat price (expect below 0)
  hunger   share of years with any household short of its food floor
  rate     median interest rate; residual: largest money and goods conservation residual
"""
import argparse
import math
import os
import random
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

METALS = ("iron_bar_kg", "copper_kg", "lead_kg", "bronze_kg", "tin_kg")
STATIC_BAND = 0.05


def play(civ_id, seed, years):
    sys.argv = sys.argv[:1]
    from sim import simulator
    tree, _prices, nodes, _wages, _goods = simulator.load()
    goal = tree["meta"]["goal_node"]
    _levels, order, _blocked = simulator.load_strategy("recommended", nodes, goal)
    game = simulator.Sim(nodes, order, random.Random(seed), events=True, manual=False,
                         civ=simulator.load_civ(civ_id), cfg={"agent_economy": True})
    game.goal, game.done_year = goal, {}
    rows = []
    for _year in range(years):
        if game.dead_reason:
            break
        weather = game._pooled_farm_weather_multiplier(game.state.scenario.year)
        game.step()
        agent = game.economy.agent
        prices, wages, rate = agent.answers()
        record = agent.economy().record
        hungry = any(cohort.unmet_floor_by_need.get("food", 0.0) > 0.0 for cohort in record.cohorts.values())
        traded = {key.split("|", 1)[0] for key, volume in record.volumes.items() if volume > 0.0}
        residual = record.book.check_conservation(1e-9)
        rows.append(dict(weather=weather, prices=dict(prices), wage=wages.get("labourer"), rate=rate,
                         hungry=hungry, traded=traded,
                         residual=max([abs(value) for value in list(residual.money.values()) + list(residual.goods.values())] or [0.0])))
    return rows


def volatility(series):
    changes = [math.log(after / before) for before, after in zip(series, series[1:]) if before > 0.0 and after > 0.0]
    return statistics.pstdev(changes) if len(changes) > 1 else float("nan")


def summarise(rows):
    first = rows[0]["prices"]
    traded = set.intersection(*[row["traded"] for row in rows]) if rows else set()
    static = [good for good in traded if good in first and first[good] > 0.0
              and all(abs(row["prices"].get(good, 0.0) / first[good] - 1.0) <= STATIC_BAND for row in rows)]
    wheat = [row["prices"].get("wheat_kg", float("nan")) for row in rows]
    metals = [volatility([row["prices"].get(metal, float("nan")) for row in rows]) for metal in METALS
              if all(metal in row["prices"] for row in rows)]
    metals = [value for value in metals if not math.isnan(value)]
    wages = [row["wage"] / row["prices"]["wheat_kg"] for row in rows
             if row["wage"] and row["prices"].get("wheat_kg")]
    weather = [row["weather"] for row in rows[1:]]
    wheat_change = [math.log(after / before) for before, after in zip(wheat, wheat[1:])]
    return dict(static=len(static) / len(traded) if traded else float("nan"),
                traded=len(traded),
                grain_volatility=volatility(wheat),
                metal_volatility=statistics.median(metals) if metals else float("nan"),
                wage_kg_wheat_per_hour=statistics.median(wages) if wages else float("nan"),
                harvest_correlation=_correlation(weather, wheat_change),
                hungry_years=sum(row["hungry"] for row in rows) / len(rows),
                rate=statistics.median(row["rate"] or 0.0 for row in rows),
                residual=max(row["residual"] for row in rows))


def _correlation(first, second):
    pairs = [(a, b) for a, b in zip(first, second) if not (math.isnan(a) or math.isnan(b))]
    if len(pairs) < 3:
        return float("nan")
    xs, ys = zip(*pairs)
    mean_x, mean_y = statistics.fmean(xs), statistics.fmean(ys)
    cov = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    spread = math.sqrt(sum((x - mean_x) ** 2 for x in xs) * sum((y - mean_y) ** 2 for y in ys))
    return cov / spread if spread > 0.0 else float("nan")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--years", type=int, default=40)
    parser.add_argument("--seeds", default="1,2,3")
    parser.add_argument("--civs", default="", help="comma-separated; every civilisation when empty")
    arguments = parser.parse_args(argv)
    from sim.engine import data
    civs = [civ for civ in arguments.civs.split(",") if civ] or sorted(
        name[:-5] for name in os.listdir(data.CIVDIR) if name.endswith(".json") and not name.startswith("_"))
    columns = ("static", "traded", "grain_volatility", "metal_volatility", "wage_kg_wheat_per_hour",
               "harvest_correlation", "hungry_years", "rate", "residual")
    print("%-18s %4s %6s  " % ("civilisation", "seed", "secs") + "  ".join("%10s" % column[:10] for column in columns))
    for civ in civs:
        for seed in [int(seed) for seed in arguments.seeds.split(",") if seed]:
            started = time.time()
            summary = summarise(play(civ, seed, arguments.years))
            print("%-18s %4d %6.0f  " % (civ, seed, time.time() - started)
                  + "  ".join("%10.3g" % summary[column] for column in columns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
