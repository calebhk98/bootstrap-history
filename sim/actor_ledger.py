#!/usr/bin/env python3
"""actor_ledger.py: where each non-founder actor's money came from and went.

    python3 sim/actor_ledger.py                        Rome, 100 years, seed 1
    python3 sim/actor_ledger.py han_china_100ad 200 3  civilisation, years, seed

Prints the government's and the firms' income and outlays by purpose, and each
purpose's share of the total. The numbers are measured from the run, not kept
in any document.
"""
import os
import random
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

from sim import simulator as S  # noqa: E402


def totals(records):
	income, outlays = {}, {}
	for record in records:
		for label, amount in record.income.items():
			income[label] = income.get(label, 0.0) + amount
		for label, amount in record.outlays.items():
			outlays[label] = outlays.get(label, 0.0) + amount
	return income, outlays


def show(title, records):
	income, outlays = totals(records)
	print("%s (%d actors)" % (title, len(records)))
	for heading, table in (("income", income), ("outlays", outlays)):
		total = sum(table.values()) or 1.0
		for label, amount in sorted(table.items(), key=lambda item: -item[1]):
			print("  %-8s %-16s %16.0f  %5.1f%%" % (heading, label, amount, 100.0 * amount / total))


def main(argv):
	civ_id = argv[1] if len(argv) > 1 else "rome_100ad"
	years = int(argv[2]) if len(argv) > 2 else 100
	seed = int(argv[3]) if len(argv) > 3 else 1
	tree, _prices, nodes, _wages, _goods = S.load()
	goal = tree["meta"]["goal_node"]
	_lab, order, _b = S.load_strategy("recommended", nodes, goal)
	game = S.Sim(nodes, order, random.Random(seed), events=True, manual=False, civ=S.load_civ(civ_id))
	game.goal, game.done_year = goal, {}
	for _ in range(years):
		if game.dead_reason:
			break
		game.step()
	records = game.state.actors.records
	show("governments", [r for r in records.values() if r.kind == "government"])
	show("firms", [r for r in records.values() if r.kind == "firm"])
	return 0


if __name__ == "__main__":
	sys.exit(main(sys.argv))
