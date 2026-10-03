"""capacity_remedies: regression checks, run individually with `--only capacity_remedies`."""
from .harness import *  # noqa: F401,F403

from sim.ui.proto.render_screens_economy import render_capacity

# Complaint 90: the capacity screen offers the commands that would end each shortage.

test_sim = sim(capital=1e7)
for node_id in list(ORDER)[:400]:
    test_sim.active[node_id] = dict(ph_left=float(NODES[node_id]["ph"]), yrs=0.0, spent=0.0, cost_left=0.0,
                                    lab_left={trade: 0.0 for trade in NODES[node_id].get("lab", {})})

capacity = S._agent_dispatch(test_sim, NODES, {"cmd": "capacity"})
short = [row["material"] for row in capacity["resources"] if row["surplus_t_per_yr"] < 0]
remedies = {row["shortage"]: row for row in capacity.get("remedies") or []}

check("every short material has a remedy row", bool(short) and all(name in remedies for name in short),
      (short, sorted(remedies)))
check("a mined material offers a quote and a buy command",
      any(command.startswith("quote mine coal") for command in remedies.get("coal", {}).get("commands", []))
      and any(command.startswith("buy mine coal") for command in remedies.get("coal", {}).get("commands", [])),
      remedies.get("coal"))
check("saltpetre offers nitre beds",
      any(command.startswith("buy nitre") for command in remedies.get("saltpetre", {}).get("commands", [])),
      remedies.get("saltpetre"))
check("the commands are the ones shortage_remedy already names",
      all(command in test_sim.shortage_remedy("coal") for command in remedies.get("coal", {}).get("commands", ["x"])),
      remedies.get("coal"))

text = render_capacity(capacity)
check("the rendered capacity screen shows the commands under the shortage",
      "buy mine coal" in text, text[-800:])

# A trade short of hours: hire it, and house the hires when there is no room.
try:
    from sim.ui.proto.capacity_remedies import capacity_remedies
except ImportError:
    def capacity_remedies(*_args):
        return []
trade_rows = [{"trade": "smith", "demand_hours_this_year": 300000.0, "supply_hours_this_year": 1000.0,
               "oversubscribed": True, "projects_drawing_on_it": []}]
rows = capacity_remedies(test_sim, [], trade_rows)
commands = rows[0]["commands"] if rows else []
check("an oversubscribed trade offers hiring it", any(command.startswith("hire smith") for command in commands), rows)
check("...and housing when the household has no room for that many",
      any(command.startswith("buy housing") for command in commands), rows)

# Complaint 189: one shortfall per material, so the suggested size covers what the row reports.
import math
import re

for row in capacity["resources"]:
    if row["surplus_t_per_yr"] >= 0 or row["material"] not in ("coal", "iron", "copper", "lead", "tin", "silver"):
        continue
    remedy = remedies[row["material"]]
    bought = [int(match) for command in remedy["commands"]
              for match in re.findall(r"^buy mine \w+ (\d+)$", command)]
    check("the suggested %s mine covers the shortfall the row reports" % row["material"],
          bool(bought) and bought[0] >= -row["surplus_t_per_yr"] - 0.05,
          (row, remedy))
    check("...and the remedy sentence states the same shortfall for %s" % row["material"],
          "{:,.0f}".format(-row["surplus_t_per_yr"]) in remedy["how"], (row, remedy["how"]))
