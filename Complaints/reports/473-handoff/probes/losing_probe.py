"""The recipes whose makers lose money on average over their remembered years, late in a member's spin-up: revenue, earnings
as a share of revenue, capacity, expected sales, runs staffed and worked (shares of the opening's expected sales), and their wage bill.
Usage: python3 losing_probe.py <civ> <member> <years>"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import spin_up_stages
from sim.markets.spin_up_ensemble import cash_factor

civ, member, years = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
if cash_factor(member) != 1.0:
    spin_up_stages.perturb_household_cash(economy, cash_factor(member))
inputs = spin_up_stages.year_inputs(economy)
record = economy.record
opening = defaultdict(float)
for producer in record.producers.values():
    opening[producer.recipe_id] += producer.expected_sales
for year in range(years):
    outcome = economy.step(inputs)
rows = defaultdict(lambda: defaultdict(float))
for producer in record.producers.values():
    row = rows[producer.recipe_id]
    history = producer.net_earnings_history
    revenues = producer.revenue_history
    row["earnings"] += sum(history) / len(history) if history else 0.0
    row["revenue"] += sum(revenues) / len(revenues) if revenues else 0.0
    row["capacity"] += producer.capacity_runs
    row["expected"] += producer.expected_sales
    row["worked"] += max(producer.last_runs, 0.0)
    row["staffed"] += producer.staffed_runs or 0.0
    hours = sum(setup.recipes[producer.recipe_id].labour_hours.values())
    row["staffed_hours"] += (producer.staffed_runs or 0.0) * hours
    row["worked_hours"] += max(producer.last_runs, 0.0) * hours
total_revenue = sum(row["revenue"] for row in rows.values())
print("after", years, "years; total remembered revenue %.4g, total earnings %.4g" % (total_revenue, sum(row["earnings"] for row in rows.values())))
print("%-34s %8s %9s %6s %6s %7s %6s" % ("recipe", "rev share", "earn/rev", "cap", "exp", "staffed", "worked"))
for recipe_id, row in sorted(rows.items(), key=lambda item: item[1]["earnings"])[:22]:
    base = opening[recipe_id] or 1.0
    print("%-34s %8.4f %9.3f %6.2f %6.2f %7.2f %6.2f" % (recipe_id[:34], row["revenue"] / total_revenue, row["earnings"] / row["revenue"] if row["revenue"] else float("nan"),
          row["capacity"] / base, row["expected"] / base, row["staffed"] / base, row["worked"] / base))

staffed_total = sum(row["staffed_hours"] for row in rows.values())
worked_total = sum(row["worked_hours"] for row in rows.values())
print("hours staffed %.4g, hours the worked runs take at the recipes' own hours %.4g: %.1f%% of staffed hours stood idle or went on hand work" % (
    staffed_total, worked_total, 100 * (1 - worked_total / staffed_total)))
print("largest gaps between staffed and worked hours:")
for recipe_id, row in sorted(rows.items(), key=lambda item: item[1]["worked_hours"] - item[1]["staffed_hours"])[:12]:
    print("   %-34s %5.2f%% of all staffed hours (staffed %.3g, worked %.3g)" % (recipe_id[:34], 100 * (row["staffed_hours"] - row["worked_hours"]) / staffed_total, row["staffed_hours"], row["worked_hours"]))
