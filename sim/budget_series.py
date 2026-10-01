#!/usr/bin/env python3
"""budget_series.py: the state's budget year by year, summarised by decade.

    python3 sim/budget_series.py <civilisation id> <years> <seed> [rows.jsonl]
    python3 sim/budget_series.py rows.jsonl      summarise rows a cut-off run wrote

Set BUDGET_SERIES_IDLE_FOUNDER=1 to leave the founder idle (a fast run of the state alone).
Prints, for each decade, the state's revenue, each spending line, surplus or
deficit, the levy rates it sets, the army it keeps and what it took from the
founder. Everything is measured from the run, not kept in any document.
"""
import json
import os
import random
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
	sys.path.insert(0, REPO_ROOT)

from sim import simulator as S  # noqa: E402
from sim.engine.actors import SimWorld  # noqa: E402
from sim.engine.default_civilisation import default_civilisation_id  # noqa: E402


def run(civ_id, years, seed, out_path=None):
	"""One row per simulated year; with `out_path`, each row is also appended there as a JSON line
	as it is made, so a long run that is cut off still leaves its years."""
	tree, _prices, nodes, _wages, _goods = S.load()
	goal = tree["meta"]["goal_node"]
	_lab, order, _b = S.load_strategy("recommended", nodes, goal)
	game = S.Sim(nodes, order, random.Random(seed), events=True, manual=bool(os.environ.get("BUDGET_SERIES_IDLE_FOUNDER")), civ=S.load_civ(civ_id))
	game.goal, game.done_year = goal, {}
	treasury = game.state_treasury()
	rows = []
	taken_before = 0.0
	for _ in range(years):
		if game.dead_reason:
			break
		game.step()
		record = treasury.record
		taken = record.income.get("requisition", 0.0) + record.income.get("office", 0.0)
		rows.append({
			"year": game.state.scenario.year,
			"revenue": SimWorld(game).state_revenue(),
			"need": dict(record.need),
			"unfunded": dict(record.unfunded),
			"reserve": record.money,
			"army": record.army,
			"requisition_rate": record.levy_requisition_rate,
			"office_rate": record.levy_office_rate,
			"founder_levy": taken - taken_before,
			"founder_income": game.revenue(),
		})
		taken_before = taken
		if out_path:
			with open(out_path, "a") as handle:
				handle.write(json.dumps(rows[-1]) + "\n")
	return rows


def decades(rows):
	for start in range(0, len(rows), 10):
		chunk = rows[start:start + 10]
		yield chunk


def show(rows):
	lines = sorted({name for row in rows for name in row["need"]})
	print("%-6s %12s %12s %9s %7s %7s %10s %12s %s" % (
		"year", "revenue", "need", "unfunded", "req", "off", "army", "founder_levy", " ".join(lines)))
	for chunk in decades(rows):
		count = float(len(chunk))
		mean = lambda key: sum(row[key] for row in chunk) / count  # noqa: E731
		need = sum(sum(row["need"].values()) for row in chunk) / count
		unfunded = sum(sum(row["unfunded"].values()) for row in chunk) / count
		per_line = [sum(row["need"].get(name, 0.0) for row in chunk) / count for name in lines]
		print("%-6d %12.4g %12.4g %9.3g %7.3f %7.3f %10.0f %12.4g %s" % (
			chunk[0]["year"], mean("revenue"), need, unfunded, mean("requisition_rate"),
			mean("office_rate"), mean("army"), mean("founder_levy"),
			" ".join("%.3g" % value for value in per_line)))
	fired = sum(1 for row in rows if row["requisition_rate"] + row["office_rate"] > 0.0)
	ceiling = sum(1 for row in rows if row["requisition_rate"] + row["office_rate"] >= 0.2999)
	short = sum(1 for row in rows if sum(row["unfunded"].values()) > 0.0)
	print("years %d, state went short %d, levy fired %d, at ceiling %d" % (len(rows), short, fired, ceiling))


def main(argv):
	civ_id = argv[1] if len(argv) > 1 else default_civilisation_id()
	years = int(argv[2]) if len(argv) > 2 else 200
	seed = int(argv[3]) if len(argv) > 3 else 1
	out_path = argv[4] if len(argv) > 4 else None
	if civ_id.endswith(".jsonl"):  # summarise rows a run already wrote
		with open(civ_id) as handle:
			show([json.loads(line) for line in handle])
		return 0
	rows = run(civ_id, years, seed, out_path)
	show(rows)
	return 0


if __name__ == "__main__":
	sys.exit(main(sys.argv))
