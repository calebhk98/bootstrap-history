"""Scenario: the capacity screen on a whole game names a remedy for every short material and sizes it to the reported
shortfall (Complaints 90, 189). The rules are in test_capacity_remedies."""
from .harness import *  # noqa: F401,F403

import re

test_sim = sim(capital=1e7)
for node_id in list(ORDER)[:400]:
    test_sim.active[node_id] = dict(ph_left=float(NODES[node_id]["ph"]), yrs=0.0, spent=0.0, cost_left=0.0,
                                    lab_left={trade: 0.0 for trade in NODES[node_id].get("lab", {})})
capacity = S._agent_dispatch(test_sim, NODES, {"cmd": "capacity"})
remedies = {row["shortage"]: row for row in capacity.get("remedies") or []}
short_rows = [row for row in capacity["resources"] if row["surplus_t_per_yr"] < 0]
check("scenario: every short material on the capacity screen has a remedy row",
      bool(short_rows) and all(row["material"] in remedies for row in short_rows), (short_rows, sorted(remedies)))
for row in short_rows:
    if row["material"] not in ("coal", "iron", "copper", "lead", "tin", "silver"):
        continue
    bought = [int(match) for command in remedies[row["material"]]["commands"]
              for match in re.findall(r"^buy mine \w+ (\d+)$", command)]
    check("scenario: the suggested %s mine covers the shortfall the row reports" % row["material"],
          bool(bought) and bought[0] >= -row["surplus_t_per_yr"] - 0.05, (row, remedies[row["material"]]))
