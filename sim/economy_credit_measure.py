#!/usr/bin/env python3
"""Loans against the money stock, and the base rate, over a run of the agent economy.

    python3 sim/economy_credit_measure.py --years 20 --civs england_1300,rome_100ad --seed 1

Columns: claims (principal plus arrears) as a share of the money stock at the end and at the
highest point, the median and highest base rate, the mean share of people short of food, and
which kinds of agent held loans as borrowers.
"""
import argparse
import os
import random
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def measure(civ_id, seed, years):
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
        game.step()
        economy = game.economy.agent.economy()
        record = economy.record
        currency = economy.setup.currency_id
        money = record.book.money_supply(currency)
        claims = sum(loan.principal + loan.arrears for loan in record.loans)
        people = sum(cohort.people for cohort in record.cohorts.values())
        hungry = sum(cohort.people for cohort in record.cohorts.values()
                     if cohort.unmet_floor_by_need.get("food", 0.0) > 0.0) / max(people, 1e-9)
        rows.append((claims / money if money else 0.0, record.memory.rates.get(currency, 0.0), hungry,
                     {loan.borrower.split(":")[0] for loan in record.loans}))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--years", type=int, default=20)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--civs", default="england_1300,rome_100ad")
    arguments = parser.parse_args(argv)
    print("%-14s %9s %9s %9s %9s %8s  %s" % ("civilisation", "loans/$", "max", "rate med", "rate max", "hungry",
                                             "borrower kinds"))
    for civ in arguments.civs.split(","):
        rows = measure(civ, arguments.seed, arguments.years)
        kinds = sorted(set().union(*[row[3] for row in rows]))
        print("%-14s %9.5f %9.5f %9.3f %9.3f %8.3f  %s" % (
            civ, rows[-1][0], max(row[0] for row in rows), statistics.median(row[1] for row in rows),
            max(row[1] for row in rows), statistics.fmean(row[2] for row in rows), ",".join(kinds)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
