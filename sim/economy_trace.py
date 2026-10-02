#!/usr/bin/env python3
"""Run the agent economy alone for a civilisation and print how prices, wages and money move.

    python3 sim/economy_trace.py <civilisation> 30
    python3 sim/economy_trace.py <civilisation> 20 --goods wheat_kg,silver_kg,iron_bar_kg

`wage/h` is the unskilled wage and `wheat/h` what an hour of it buys in kg of wheat.
The engine supplies the opening (tiles, people, recipes in use, opening prices and wages); after that
only the economy runs, with population and yields held at the opening.
"""
import argparse
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DEFAULT_GOODS = "wheat_kg,silver_kg,iron_bar_kg,cloth_kg,olive_oil_kg"


def opening_sim(civ_id):
    sys.argv = sys.argv[:1]
    from sim import simulator
    tree, _prices, nodes, _wages, _goods = simulator.load()
    goal = tree["meta"]["goal_node"]
    _levels, order, _blocked = simulator.load_strategy("recommended", nodes, goal)
    return simulator.Sim(nodes, order, random.Random(1), events=False, manual=False, civ=simulator.load_civ(civ_id))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("civilisation")
    parser.add_argument("years", type=int, nargs="?", default=20)
    parser.add_argument("--goods", default=DEFAULT_GOODS, help="comma-separated goods to show")
    arguments = parser.parse_args(argv)
    from sim.engine.economy_port_setup import build_setup
    from sim.economy.economy import Economy
    from sim.economy.protocols import YearInputs
    sim = opening_sim(arguments.civilisation)
    started = time.time()
    setup = build_setup(sim)
    economy = Economy(setup)
    opened = time.time()
    record = economy.record
    print("opening: %d tiles, %d cohorts, %d producers, %d merchants, %d recipes, %d areas for wheat; %.1fs"
          % (len(setup.tiles), len(record.cohorts), len(record.producers), len(record.merchants),
             len(setup.recipes), len(economy.area_map.areas("wheat_kg")) if "wheat_kg" in economy.area_map.goods() else 0,
             opened - started))
    goods = [good for good in arguments.goods.split(",") if good]
    print("year  level   rate   money      wage/h  wheat/h  " + "  ".join("%12s" % good[:12] for good in goods)
          + "   residual  secs")
    for year in range(arguments.years):
        tick = time.time()
        outcome = economy.step(YearInputs(year=year, population_by_tile={}, working_age_share=setup.working_share,
                                          yield_factor_by_producer={}, engine_orders={}))
        wage = outcome.wages.get(setup.unskilled_trade, float("nan"))
        wheat = outcome.prices.get("wheat_kg")
        print("%4d  %5.3f  %5.3f  %10.4g  %7.4g  %7.3g  " % (outcome.year, outcome.price_level, outcome.rate,
                                                           outcome.money_supply, wage,
                                                           wage / wheat if wheat else float("nan"))
              + "  ".join("%12.5g" % outcome.prices.get(good, float("nan")) for good in goods)
              + "   %.1e  %.2f" % (outcome.conservation_residual, time.time() - tick))
    return 0


if __name__ == "__main__":
    sys.exit(main())
