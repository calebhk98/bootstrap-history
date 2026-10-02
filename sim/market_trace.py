"""Prices the market posts (labour hours), price level, output per head, capital, firms and CPU, by decade.

    python3 sim/market_trace.py rome_100ad [years]

Seed 1, events on. Used to compare a change to the market against the branch it started from."""
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim import simulator as S
TREE, PRICES, NODES, WAGES, GOODS = S.load()
GOAL = TREE["meta"]["goal_node"]
_L, ORDER, _B = S.load_strategy("recommended", NODES, GOAL)
STAPLES = ["wheat_kg", "iron_bloom_kg", "iron_bar_kg", "pig_iron_kg", "cast_iron_kg"]

def run(civ, years, marks):
    sim = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ(civ))
    sim.goal, sim.done_year = GOAL, {}
    start = time.process_time()
    rows = []
    for year in range(1, years + 1):
        if sim.dead_reason:
            break
        sim.step()
        if year in marks:
            mph = sim.money_per_labour_hour()
            prices = sim._material_prices()
            posted = {m: round(prices[m] * sim.market_price_ratio(m) / mph, 4) for m in STAPLES if m in prices}
            firms = len(sim.actors.active_firms()) if sim.state.actors is not None else 0
            rows.append((year, "level", round(sim.home_price_level(), 3), posted, round(float(sim.real_output_per_head()), 4), round(float(sim.state.household.capital), 1), firms,
                         round(time.process_time() - start, 1)))
    return rows

if __name__ == "__main__":
    civ = sys.argv[1]
    horizon = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    for row in run(civ, horizon, {1, horizon // 3, 2 * horizon // 3, horizon}):
        print(civ, row)
